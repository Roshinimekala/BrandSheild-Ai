"""Look-alike name detection and risk scoring.

Everything here is pure Python (plus rapidfuzz) and explainable: every score
comes with a list of human-readable reasons.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import fuzzy

# Characters attackers swap in for look-alike names.
HOMOGLYPHS = {
    "0": "o", "1": "l", "!": "i", "|": "l", "$": "s", "5": "s", "3": "e",
    "4": "a", "@": "a", "7": "t", "8": "b", "9": "g",
    # Cyrillic / Greek look-alikes
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s", "һ": "h", "ԁ": "d", "ɡ": "g", "ο": "o",
    "ν": "v", "ρ": "p", "τ": "t", "α": "a",
}
# Multi-character tricks, applied before single-char mapping.
MULTI_CHAR = [("rn", "m"), ("vv", "w"), ("cl", "d"), ("ii", "u")]

# Words scammers append to a brand to look "official".
SUSPICIOUS_WORDS = {
    "official", "support", "care", "help", "helpdesk", "customer", "service",
    "team", "india", "app", "online", "verified", "login", "secure", "rewards",
    "offers", "giveaway", "claim", "wallet", "pay", "bank", "loans", "jobs",
    "careers", "hq", "real", "original", "new",
}


@dataclass
class NameMatch:
    score: float  # 0..1 name similarity (higher = more look-alike)
    exact: bool = False
    reasons: list[str] = field(default_factory=list)


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def basic_normalize(text: str) -> str:
    """Lowercase, strip accents, drop everything except letters/digits/spaces."""
    text = strip_accents(text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def deobfuscate(text: str) -> str:
    """Collapse homoglyphs and rn->m style tricks into a canonical form."""
    text = strip_accents(text).lower()
    for src, dst in MULTI_CHAR:
        text = text.replace(src, dst)
    return "".join(HOMOGLYPHS.get(c, c) for c in text)


def squash(text: str) -> str:
    """Remove all non-alphanumerics: 'Pay-Tm' / 'pay tm' / 'pay_tm' -> 'paytm'."""
    return re.sub(r"[^a-z0-9]", "", deobfuscate(basic_normalize(text)))


def _tokens(text: str) -> list[str]:
    return [t for t in basic_normalize(text).split() if t]


def compare_names(candidate: str, brand: str) -> NameMatch:
    """Score how much `candidate` looks like an impersonation of `brand`."""
    cand_basic, brand_basic = basic_normalize(candidate), basic_normalize(brand)
    if not cand_basic or not brand_basic:
        return NameMatch(0.0)

    # Identical after basic normalization -> same name (could be official or a
    # straight copy; the allowlist decides which).
    if cand_basic == brand_basic:
        return NameMatch(1.0, exact=True, reasons=["Name is identical to the brand name"])

    cand_sq, brand_sq = squash(candidate), squash(brand)
    reasons: list[str] = []
    score = 0.0

    # 1) Spacing / punctuation changes: "pay tm", "pay-tm", "p.a.y.t.m"
    if cand_sq == brand_sq:
        if cand_basic.replace(" ", "") == brand_basic.replace(" ", ""):
            reasons.append("Spacing or punctuation changed from the brand name")
            score = 0.92
        else:
            reasons.append("Character swaps (look-alike characters) used in the brand name")
            score = 0.95
        return NameMatch(score, reasons=reasons)

    # 2) Brand embedded in candidate with extra words: "Paytm Official Support"
    brand_tokens = brand_basic.split()
    cand_tokens = _tokens(candidate)
    cand_deob = [deobfuscate(t) for t in cand_tokens]
    brand_deob = [deobfuscate(t) for t in brand_tokens]

    contains_brand = False
    n = len(brand_deob)
    if n and any(cand_deob[i : i + n] == brand_deob for i in range(len(cand_deob) - n + 1)):
        contains_brand = True
    elif brand_sq and brand_sq in cand_sq and len(cand_sq) > len(brand_sq):
        contains_brand = True

    if contains_brand:
        # Tokens that are just fragments of a spaced-out brand ("pay" + "tm")
        # are part of the brand, not extra words.
        extras = [
            t for t in cand_tokens
            if deobfuscate(t) not in brand_deob and deobfuscate(t) not in brand_sq
        ]
        sus = [t for t in extras if t in SUSPICIOUS_WORDS]
        if sus:
            reasons.append(f"Brand name combined with trust-bait words: {', '.join(sus)}")
            score = 0.88
        elif extras:
            reasons.append(f"Brand name with added words: {', '.join(extras)}")
            score = 0.72
        else:
            reasons.append("Brand name embedded in a longer name")
            score = 0.7
        return NameMatch(score, reasons=reasons)

    # 3) Near-misses: typos, transpositions, one-char edits.
    cand_d, brand_d = deobfuscate(cand_sq), deobfuscate(brand_sq)
    lev = fuzzy.levenshtein(cand_d, brand_d)
    jw = fuzzy.jaro_winkler(cand_d, brand_d)
    ratio = fuzzy.ratio(cand_d, brand_d) / 100.0
    tsr = fuzzy.token_set_ratio(deobfuscate(cand_basic), deobfuscate(brand_basic)) / 100.0

    max_len = max(len(cand_d), len(brand_d))
    # Short brands can't tolerate much edit distance without false positives.
    allowed = 1 if max_len <= 6 else 2 if max_len <= 12 else 3
    if lev <= allowed and ratio >= 0.8:
        reasons.append(f"Within {lev} character edit(s) of the brand name (typo-squat)")
        score = max(0.75, ratio)
    elif jw >= 0.92 and ratio >= 0.85:
        reasons.append("Very high string similarity to the brand name")
        score = jw * 0.9
    elif tsr >= 0.9 and len(cand_tokens) > 1 and len(brand_tokens) > 1:
        reasons.append("Same words as the brand name in a different order/shape")
        score = tsr * 0.8

    return NameMatch(round(min(score, 1.0), 3), reasons=reasons)


def text_similarity(a: str, b: str) -> float:
    """Description/branding similarity 0..1 (token-set ratio, order-insensitive)."""
    if not a or not b:
        return 0.0
    return fuzzy.token_set_ratio(basic_normalize(a), basic_normalize(b)) / 100.0


# ---------------------------------------------------------------- scoring

# Evidence beyond the name (each 0..1, weights sum to 1).
EVIDENCE_WEIGHTS = {"publisher": 0.40, "description": 0.15, "logo": 0.20, "scam": 0.25}

# Phrases that show up in scam bios / app descriptions (credential or fee grabs).
SCAM_PHRASES = [
    "otp", "upi pin", "pin and", "registration fee", "processing fee", "security deposit",
    "claim your reward", "claim now", "click the link in bio", "refund instantly",
    "work from home", "without documents", "share your", "dm us", "cashback!",
]


def scam_signal(text: str) -> tuple[float, list[str]]:
    t = basic_normalize(text or "")
    hits = [p for p in SCAM_PHRASES if basic_normalize(p) in t]
    return min(1.0, 0.5 * len(hits)), hits
FLAG_THRESHOLD = 0.55  # below this we don't surface a candidate at all


def _level(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.65:
        return "medium"
    return "low"


def is_official(candidate: dict, official_handles: set[str], official_ids: set[str]) -> bool:
    """Allowlist check: official assets must never be flagged."""
    ident = str(candidate.get("id", "")).lower()
    handle = str(candidate.get("handle", "")).lower().lstrip("@")
    return ident in official_ids or (handle and handle in official_handles)


def score_candidate(candidate: dict, profile: dict) -> dict | None:
    """Return a detection dict, or None when the candidate is official/benign.

    candidate keys: kind ('social'|'app'), id, name, handle?, publisher?,
                    description?, source
    profile keys:   name, official_handles[], official_app_ids[],
                    official_publishers[], keywords[]
    """
    official_handles = {h.lower().lstrip("@") for h in profile.get("official_handles", [])}
    official_ids = {i.lower() for i in profile.get("official_app_ids", [])}
    official_ids |= {h.lower() for h in profile.get("official_handles", [])}

    if is_official(candidate, official_handles, official_ids):
        return None

    names_to_check = [profile["name"], *profile.get("keywords", [])]
    best = max(
        (compare_names(candidate["name"], n) for n in names_to_check),
        key=lambda m: m.score,
    )
    # Handles are a second chance to catch impersonation (e.g. @paytm_support_help).
    if candidate.get("handle"):
        hm = max(
            (compare_names(candidate["handle"].lstrip("@").replace("_", " "), n) for n in names_to_check),
            key=lambda m: m.score,
        )
        if hm.score > best.score:
            best = NameMatch(hm.score, hm.exact, [f"Handle: {r}" for r in hm.reasons])

    if best.score < 0.5:
        return None

    reasons = list(best.reasons)
    parts = {"name": best.score, "publisher": 0.0, "description": 0.0, "logo": 0.0, "scam": 0.0}

    sval, shits = scam_signal(candidate.get("description", ""))
    if sval:
        parts["scam"] = sval
        reasons.append("Description contains scam-style language: " + ", ".join(f"'{h}'" for h in shits[:3]))

    # Publisher mismatch (apps) - a lookalike from an unknown publisher is the red flag.
    publisher = (candidate.get("publisher") or "").strip()
    official_pubs = [p for p in profile.get("official_publishers", []) if p]
    if candidate["kind"] == "app" and publisher:
        if official_pubs and max(
            fuzzy.token_set_ratio(basic_normalize(publisher), basic_normalize(p)) for p in official_pubs
        ) >= 90:
            return None  # published by the real company
        parts["publisher"] = 1.0
        reasons.append(f"Publisher '{publisher}' is not an official publisher")
    elif candidate["kind"] == "social" and candidate.get("verified") is False:
        parts["publisher"] = 0.6
        reasons.append("Account is not verified")

    # Description resembles brand copy.
    brand_blurb = " ".join([profile["name"], profile.get("description", "")])
    dsim = text_similarity(candidate.get("description", ""), brand_blurb)
    if dsim >= 0.5:
        parts["description"] = dsim
        reasons.append(f"Description closely resembles the brand's ({int(dsim * 100)}% overlap)")

    # Logo similarity (pHash distance precomputed by the source layer, if available).
    lsim = candidate.get("logo_similarity")
    if lsim is not None and lsim >= 0.8:
        parts["logo"] = lsim
        reasons.append(f"Logo is visually near-identical ({int(lsim * 100)}% similar)")

    # Name similarity sets the base; independent evidence (publisher mismatch,
    # copied description, logo match, scam language) pushes the score up.
    evidence = sum(EVIDENCE_WEIGHTS[k] * parts[k] for k in EVIDENCE_WEIGHTS)
    total = best.score * 0.7 + evidence * 0.45
    # A strong name match alone must still surface (as low/medium).
    total = max(total, best.score * 0.8)
    total = round(min(total, 1.0), 3)
    if total < FLAG_THRESHOLD:
        return None

    return {
        **candidate,
        "risk_score": total,
        "risk_level": _level(total),
        "reasons": reasons,
        "breakdown": {k: round(v, 2) for k, v in parts.items()},
    }
