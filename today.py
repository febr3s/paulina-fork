"""
On this day — Wikipedia REST API + Wikidata entity API, with file cache.

Uses English Wikipedia on-this-day feed for births/deaths, then ranks by
sitelinks fetched from the Wikidata entity API (no SPARQL).
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

WIKIPEDIA_ONTHISDAY_URL = "https://en.wikipedia.org/api/rest_v1/feed/onthisday"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
DEFAULT_CACHE_TTL_SECONDS = 86400
_UA = "Paulina/1.0 (today-literature; https://paulina.toolforge.org/)"

CREATIVE_KEYWORDS = frozenset({
   
    "writer", "author", "novelist", "poet", "playwright", "screenwriter", "lyricist",
    "essayist", "critic", "satirist", "biographer", "translator", "editor", "publisher",
    "librettist", "storyteller", "scribe", "rhetorician", "orator", "diarist",

    "musician", "composer", "singer", "conductor", "pianist", "violinist", "guitarist",
    "cellist", "bassist", "harpist", "organist", "saxophonist", "trumpeter", "flautist",
    "drummer", "bandleader", "songwriter", "rapper",
    
    "artist", "painter", "sculptor", "illustrator", "photographer", "engraver",
    "printmaker", "ceramicist", "draughtsman", "draughtsman", "calligrapher",
    "cartoonist", "caricaturist", "graphic", "animator",
  
    "actor", "actress", "director", "filmmaker", "producer", "comedian", "dancer",
    "choreographer", "performer", "entertainer", "magician", "puppeteer",
   
    "architect", "designer", "craftsman", "jeweller",
   
    "journalist", "reporter", "broadcaster", "editor", "columnist", "correspondent",
    "publisher", "printer",
   
    "philosopher", "historian", "scholar", "anthropologist", "folklorist", "theologian",
    "linguist", "literary", "intellectual", "academic", "professor", "teacher",
  
    "politician", "activist", "reformer", "revolutionary", "nationalist", "statesman",
    "abolitionist", "suffragist",

    "naturalist", "explorer", "adventurer",
})


@dataclass
class AuthorRow:
    qid: str
    name: str
    description: str
    year: int | None
    sitelinks: int


def _cache_path(cache_root: str, month: int, day: int, locale: str) -> Path:
    safe_locale = (locale or "en").replace(os.sep, "").replace("/", "")
    mmdd = f"{month:02d}-{day:02d}"
    return Path(cache_root) / safe_locale / f"{mmdd}.json"


def _is_creative(description: str) -> bool:
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in CREATIVE_KEYWORDS)


def _fetch_wikipedia_entries(month: int, day: int, event_type: str, user_agent: str) -> list[dict]:
    url = f"{WIKIPEDIA_ONTHISDAY_URL}/{event_type}/{month:02d}/{day:02d}"
    r = requests.get(url, headers={"User-Agent": user_agent or _UA}, timeout=(10, 30))
    r.raise_for_status()
    return r.json().get(event_type, [])


def _entries_to_rows(entries: list[dict]) -> list[AuthorRow]:
    rows: list[AuthorRow] = []
    for entry in entries:
        pages = entry.get("pages", [])
        if not pages:
            continue
        page = pages[0]
        qid = page.get("wikibase_item", "")
        if not qid:
            continue
        desc = page.get("description", "")
        if not _is_creative(desc):
            continue
        name = page.get("titles", {}).get("normalized") or page.get("title", "").replace("_", " ")
        rows.append(AuthorRow(qid=qid, name=name, description=desc, year=entry.get("year"), sitelinks=0))
    return rows


def _fetch_sitelinks(qids: list[str], user_agent: str) -> dict[str, int]:
    result: dict[str, int] = {}
    if not qids:
        return result
    headers = {"User-Agent": user_agent or _UA}
    for i in range(0, len(qids), 50):
        batch = qids[i : i + 50]
        try:
            r = requests.get(
                WIKIDATA_API_URL,
                params={"action": "wbgetentities", "ids": "|".join(batch), "props": "sitelinks", "format": "json"},
                headers=headers,
                timeout=(10, 30),
            )
            r.raise_for_status()
            for qid, entity in r.json().get("entities", {}).items():
                result[qid] = len(entity.get("sitelinks", {}))
        except requests.RequestException as exc:
            logger.warning("Sitelinks batch fetch failed: %s", exc)
    return result


def fetch_from_wikidata(month: int, day: int, locale: str, user_agent: str) -> dict[str, Any]:
    born_rows = _entries_to_rows(_fetch_wikipedia_entries(month, day, "births", user_agent))
    died_rows = _entries_to_rows(_fetch_wikipedia_entries(month, day, "deaths", user_agent))

    all_qids = list({r.qid for r in born_rows + died_rows})
    sitelinks = _fetch_sitelinks(all_qids, user_agent)
    sitelinks_ok = bool(sitelinks and any(v > 0 for v in sitelinks.values()))
    for r in born_rows + died_rows:
        r.sitelinks = sitelinks.get(r.qid, 0)

    born_rows.sort(key=lambda r: r.sitelinks, reverse=True)
    died_rows.sort(key=lambda r: r.sitelinks, reverse=True)

    return {
        "month": month,
        "day": day,
        "locale": locale,
        "born": [asdict(x) for x in born_rows[:30]],
        "died": [asdict(x) for x in died_rows[:30]],
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        # Retry soon if sitelinks fetch silently failed (all zeros).
        "cache_ttl_seconds": DEFAULT_CACHE_TTL_SECONDS if sitelinks_ok else 600,
    }


def _write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def _read_cache(path: Path) -> dict[str, Any] | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _needs_refresh(path: Path, ttl_seconds: int) -> bool:
    if not path.is_file():
        return True
    age = time.time() - path.stat().st_mtime
    return age > ttl_seconds


def parse_month_day_from_request(args: Any) -> tuple[int, int]:
    """
    Query params:
    - date=YYYY-MM-DD (from HTML date input; year ignored except leap day)
    - month= & day= (integers)
    Default: today.
    """
    raw_date = args.get("date")
    if raw_date:
        parts = str(raw_date).strip().split("-")
        if len(parts) == 3:
            try:
                m, d = int(parts[1]), int(parts[2])
                if 1 <= m <= 12 and 1 <= d <= 31:
                    return m, d
            except ValueError:
                pass
    m_raw, d_raw = args.get("month"), args.get("day")
    if m_raw is not None and d_raw is not None:
        try:
            m, d = int(m_raw), int(d_raw)
            if 1 <= m <= 12 and 1 <= d <= 31:
                date(2024, m, d)
                return m, d
        except (ValueError, TypeError):
            pass
    today = date.today()
    return today.month, today.day



def featured_authors(born: list[dict], died: list[dict]) -> list[tuple[dict, str]]:
    """Return up to 3 featured (author, event) tuples: overall top, top born, top died."""
    result: list[tuple[dict, str]] = []
    seen: set[str] = set()

    def _add_top(lst: list[dict], event: str) -> None:
        for r in lst:
            if r["qid"] not in seen:
                result.append((r, event))
                seen.add(r["qid"])
                return

    pool = [(r, "born") for r in born] + [(r, "died") for r in died]
    if pool:
        top_r, top_event = max(pool, key=lambda x: x[0].get("sitelinks") or 0)
        result.append((top_r, top_event))
        seen.add(top_r["qid"])

    _add_top(born, "born")
    _add_top(died, "died")
    return result


def widget_entries(born: list[dict], died: list[dict], limit: int = 5) -> list[tuple[dict, str]]:
    """Merge born/died, sort by notability, tag with 'born'|'died'."""
    tagged: list[tuple[dict, str]] = [(r, "born") for r in born] + [(r, "died") for r in died]
    tagged.sort(key=lambda x: x[0].get("sitelinks") or 0, reverse=True)
    return tagged[:limit]


def get_literature_today(
    month: int,
    day: int,
    locale: str,
    user_agent: str,
    cache_root: str,
    *,
    allow_remote_fetch: bool = True,
    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Return cached snapshot for (month, day, locale)."""
    path = _cache_path(cache_root, month, day, locale)
    cached = _read_cache(path) if path.is_file() else None

    # Use the TTL stored in the cache (failure payloads use a short TTL).
    effective_ttl = int(cached.get("cache_ttl_seconds", ttl_seconds)) if cached else ttl_seconds
    needs_refresh = force_refresh or not cached or _needs_refresh(path, effective_ttl)

    if allow_remote_fetch and needs_refresh:
        try:
            payload = fetch_from_wikidata(month, day, locale, user_agent)
            _write_cache(path, payload)
            return payload
        except requests.RequestException as e:
            logger.warning("WDQS fetch failed for %02d-%02d: %s", month, day, e)
            if cached:
                cached["fetch_error"] = str(e)
                return cached
            failure_payload = {
                "month": month,
                "day": day,
                "locale": locale,
                "born": [],
                "died": [],
                "fetched_at": None,
                "fetch_error": str(e),
                "cache_ttl_seconds": 600,
            }
            _write_cache(path, failure_payload)
            return failure_payload

    if cached:
        return cached
    return {
        "month": month,
        "day": day,
        "locale": locale,
        "born": [],
        "died": [],
        "fetched_at": None,
    }
