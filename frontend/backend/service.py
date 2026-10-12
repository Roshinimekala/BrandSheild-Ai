"""Framework-independent core: brand profile validation, storage, and scanning."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from matcher import score_candidate
from sources import Source, SourceUnavailable, default_sources

DB_PATH = Path(__file__).parent.parent / "dkp.sqlite3"

DEFAULT_PROFILE = {
    "name": "Paytm",
    "description": "Paytm - India's leading payments app. Recharge, pay bills, UPI.",
    "logo_url": "",
    "official_handles": ["paytm", "paytmcare"],
    "official_app_ids": ["net.one97.paytm", "id473941634"],
    "official_publishers": ["One97 Communications Limited", "Paytm"],
    "keywords": [],
}


# ------------------------------------------------------------------ profile

def validate_profile(data: dict) -> tuple[dict, list[str]]:
    """Normalise and validate a brand profile; returns (profile, errors)."""
    errors: list[str] = []

    def as_list(v) -> list[str]:
        if isinstance(v, str):
            v = v.replace("\n", ",").split(",")
        return [x.strip() for x in (v or []) if str(x).strip()]

    profile = {
        "name": str(data.get("name", "")).strip(),
        "description": str(data.get("description", "")).strip(),
        "logo_url": str(data.get("logo_url", "")).strip(),
        "official_handles": [h.lstrip("@") for h in as_list(data.get("official_handles"))],
        "official_app_ids": as_list(data.get("official_app_ids")),
        "official_publishers": as_list(data.get("official_publishers")),
        "keywords": as_list(data.get("keywords")),
    }
    if len(profile["name"]) < 2:
        errors.append("Brand name is required (at least 2 characters).")
    if not profile["official_handles"] and not profile["official_app_ids"]:
        errors.append(
            "Add at least one official social handle or app ID so official assets are not flagged."
        )
    if profile["logo_url"] and not profile["logo_url"].startswith(("http://", "https://")):
        errors.append("Logo URL must start with http:// or https://.")
    return profile, errors


# ------------------------------------------------------------------ storage

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT)")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS scans (
               id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, result TEXT)"""
    )
    return conn


def get_profile() -> dict:
    with _conn() as c:
        row = c.execute("SELECT data FROM profile WHERE id = 1").fetchone()
    return json.loads(row["data"]) if row else dict(DEFAULT_PROFILE)


def save_profile(profile: dict) -> None:
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO profile (id, data) VALUES (1, ?)", (json.dumps(profile),))


def latest_scan() -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT result FROM scans ORDER BY id DESC LIMIT 1").fetchone()
    return json.loads(row["result"]) if row else None


# ------------------------------------------------------------------ scanning

def run_scan(profile: dict, sources: list[Source] | None = None, live: bool = False) -> dict:
    """Query every source, score candidates, exclude official assets."""
    sources = sources if sources is not None else default_sources(live=live)
    queries = [profile["name"], *profile.get("keywords", [])]

    detections: list[dict] = []
    status: list[dict] = []
    scanned = excluded_official = 0

    for src in sources:
        started = time.time()
        try:
            candidates = src.search(queries)
        except SourceUnavailable as exc:
            status.append({"source": src.name, "kind": src.kind, "ok": False,
                           "error": str(exc), "live": src.live})
            continue
        except Exception as exc:  # never let one source crash the scan
            status.append({"source": src.name, "kind": src.kind, "ok": False,
                           "error": f"unexpected error: {type(exc).__name__}", "live": src.live})
            continue

        hits = 0
        for cand in candidates:
            scanned += 1
            res = score_candidate(cand, profile)
            if res is None:
                # distinguish "official" from "benign" just for the summary counter
                if (cand.get("id", "").lower() in {a.lower() for a in profile.get("official_app_ids", [])}
                        or cand.get("handle", "").lower() in {h.lower() for h in profile.get("official_handles", [])}):
                    excluded_official += 1
                continue
            hits += 1
            detections.append(res)
        status.append({"source": src.name, "kind": src.kind, "ok": True, "live": src.live,
                       "candidates": len(candidates), "flagged": hits,
                       "ms": int((time.time() - started) * 1000)})

    detections.sort(key=lambda d: d["risk_score"], reverse=True)
    result = {
        "ts": time.time(),
        "brand": profile["name"],
        "summary": {
            "scanned": scanned,
            "flagged": len(detections),
            "high": sum(d["risk_level"] == "high" for d in detections),
            "medium": sum(d["risk_level"] == "medium" for d in detections),
            "low": sum(d["risk_level"] == "low" for d in detections),
            "official_excluded": excluded_official,
        },
        "sources": status,
        "detections": detections,
    }
    with _conn() as c:
        c.execute("INSERT INTO scans (ts, result) VALUES (?, ?)", (result["ts"], json.dumps(result)))
    return result
