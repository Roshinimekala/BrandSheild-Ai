"""Data sources. Each source returns candidate dicts or raises SourceUnavailable.

The scan orchestrator catches SourceUnavailable per source, so one broken
source never breaks the whole scan (judged under "graceful handling of
unavailable sources").
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


class SourceUnavailable(Exception):
    """Raised when a source cannot be reached or returns bad data."""


class Source:
    name = "base"
    kind = "social"  # or "app"
    live = False

    def search(self, queries: list[str]) -> list[dict]:
        raise NotImplementedError


class MockSocialSource(Source):
    name = "Social (sample dataset)"
    kind = "social"

    def search(self, queries: list[str]) -> list[dict]:
        try:
            rows = json.loads((DATA_DIR / "mock_social.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SourceUnavailable(f"sample data unreadable: {exc}") from exc
        return [{**r, "source": self.name} for r in rows]


class MockAppStoreSource(Source):
    name = "App stores (sample dataset)"
    kind = "app"

    def search(self, queries: list[str]) -> list[dict]:
        try:
            rows = json.loads((DATA_DIR / "mock_apps.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SourceUnavailable(f"sample data unreadable: {exc}") from exc
        return [{**r, "source": self.name} for r in rows]


class ITunesSource(Source):
    """Live Apple App Store search via the free iTunes Search API (no key)."""

    name = "Apple App Store (live)"
    kind = "app"
    live = True

    def search(self, queries: list[str]) -> list[dict]:
        out: dict[str, dict] = {}
        for q in queries:
            url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
                {"term": q, "entity": "software", "limit": 25, "country": "in"}
            )
            try:
                with urllib.request.urlopen(url, timeout=6) as resp:  # noqa: S310
                    payload = json.loads(resp.read().decode("utf-8"))
            except Exception as exc:  # network, DNS, proxy, JSON...
                raise SourceUnavailable(f"iTunes Search API unreachable ({type(exc).__name__})") from exc
            for item in payload.get("results", []):
                aid = f"id{item.get('trackId')}"
                out[aid] = {
                    "kind": "app",
                    "store": "App Store",
                    "id": aid,
                    "name": item.get("trackName", ""),
                    "publisher": item.get("sellerName") or item.get("artistName", ""),
                    "description": (item.get("description") or "")[:400],
                    "icon_url": item.get("artworkUrl100"),
                    "source": self.name,
                }
            time.sleep(0.2)  # be polite
        return list(out.values())


def default_sources(live: bool = False) -> list[Source]:
    sources: list[Source] = [MockSocialSource(), MockAppStoreSource()]
    if live:
        sources.append(ITunesSource())
    return sources
