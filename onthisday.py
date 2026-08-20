"""
On this day — Wikipedia REST API + Wikidata entity API, with file cache.

Uses English Wikipedia on-this-day feed for births/deaths, then ranks by
sitelinks fetched from the Wikidata entity API (no SPARQL).
"""

from flask import current_app
import requests

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

import languages


WIKIPEDIA_ONTHISDAY_URL = "https://en.wikipedia.org/api/rest_v1/feed/onthisday"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

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
   
    "journalist", "reporter", "broadcaster", "columnist", "correspondent",
    " printer", # printer has a space to distiguish it from sprinter
   
    "philosopher", "historian", "scholar", "anthropologist", "folklorist", "theologian",
    "linguist", "literary", "intellectual", "academic", "professor", "teacher",
  
    "activist", "reformer", "revolutionary", "nationalist", "statesman",
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
    in_public_domain: bool


def is_creative(description: str) -> bool:
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in CREATIVE_KEYWORDS)


def entries_to_rows(entries: list[dict]) -> list[AuthorRow]:
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
        if not is_creative(desc):
            continue
        rows.append(AuthorRow(qid=qid, name="", description="", year=entry.get("year"), sitelinks=0, in_public_domain=False))
    return rows


def fetch_labels_desc_and_sitelinks(qids: list[str]) -> dict[str, int]:
    result: dict = {}
    if not qids:
        return result
    for i in range(0, len(qids), 50):
        batch = qids[i : i + 50]

        r = requests.get(
            WIKIDATA_API_URL,
            params={"action": "wbgetentities",
                    "ids": "|".join(batch),
                    "props": "labels|descriptions|sitelinks|claims",
                    "languages": languages.get_locale(),
                    "languagefallback": "",
                    "format": "json"},
            headers={"user-agent": current_app.config['USER_AGENT']},
            timeout=(10, 30),
        )

        for qid, entity in r.json().get("entities", {}).items():
            copyright_status = entity.get("claims", {}).get("P7763")
            in_public_domain = False
            if copyright_status:
                for claim in copyright_status:
                    if claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id") == "Q71887839":
                        in_public_domain = True

            result[qid] = {"sitelinks": len(entity.get("sitelinks", {})),
                           "label": entity.get('labels', {}).get(languages.get_locale(), {}).get('value'),
                           "description": entity.get('descriptions', {}).get(languages.get_locale(), {}).get('value'),
                           "in_public_domain": in_public_domain}
    return result


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


def widget_entries(born: list[dict], died: list[dict], limit: int = 4) -> list[tuple[dict, str]]:
    """Merge born/died, sort by notability, tag with 'born'|'died'."""
    tagged: list[tuple[dict, str]] = [(r, "born") for r in born] + [(r, "died") for r in died]
    tagged.sort(key=lambda x: x[0].get("sitelinks") or 0, reverse=True)
    return tagged[:limit]


def get_today_authors(month: int, day: int) -> dict[str, Any]:

    url_events = f"{WIKIPEDIA_ONTHISDAY_URL}/all/{month:02d}/{day:02d}"

    events_response = requests.get(url_events, headers={"user-agent": current_app.config['USER_AGENT']}, timeout=(10, 30))
    events = events_response.json()

    born_rows = entries_to_rows(events.get("births", []))
    died_rows = entries_to_rows(events.get("deaths", []))

    all_qids = list({r.qid for r in born_rows + died_rows})
    item_info = fetch_labels_desc_and_sitelinks(all_qids)
    for r in born_rows + died_rows:
        r.sitelinks = item_info.get(r.qid, 0).get("sitelinks", 0)
        r.name = item_info.get(r.qid, "").get("label", "")
        r.description = item_info.get(r.qid, "").get("description", "")
        r.in_public_domain = item_info.get(r.qid, False).get("in_public_domain", False)

    born_rows.sort(key=lambda r: r.sitelinks, reverse=True)
    died_rows.sort(key=lambda r: r.sitelinks, reverse=True)

    return {
        "month": month,
        "day": day,
        "born": [asdict(x) for x in born_rows],
        "died": [asdict(x) for x in died_rows],
    }


