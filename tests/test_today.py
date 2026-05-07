import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.datastructures import ImmutableMultiDict

import today as tl


def test_parse_month_day():
    args = ImmutableMultiDict([("date", "2000-05-02")])
    assert tl.parse_month_day_from_request(args) == (5, 2)


def test_literature_today_route(client, monkeypatch):
    def fake_get(*_args, **_kwargs):
        return {
            "month": 5,
            "day": 2,
            "locale": "en",
            "born": [{"qid": "Q1", "name": "Sample", "description": "", "year": 1886, "sitelinks": 10}],
            "died": [],
            "fetched_at": "2026-05-06T00:00:00Z",
        }

    monkeypatch.setattr(tl, "get_literature_today", fake_get)
    response = client.get("/today")
    assert response.status_code == 200
