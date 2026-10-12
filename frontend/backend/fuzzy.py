"""String-similarity helpers.

Uses rapidfuzz when installed (fast); otherwise falls back to small pure-Python
implementations so the prototype still runs anywhere.
"""
from __future__ import annotations

try:  # pragma: no cover - exercised implicitly depending on environment
    from rapidfuzz import fuzz as _fuzz
    from rapidfuzz.distance import JaroWinkler as _JW
    from rapidfuzz.distance import Levenshtein as _Lev

    BACKEND = "rapidfuzz"

    def levenshtein(a: str, b: str) -> int:
        return _Lev.distance(a, b)

    def jaro_winkler(a: str, b: str) -> float:
        return _JW.similarity(a, b)

    def ratio(a: str, b: str) -> float:
        """Normalised similarity 0..100."""
        return _fuzz.ratio(a, b)

    def token_set_ratio(a: str, b: str) -> float:
        return _fuzz.token_set_ratio(a, b)

except ImportError:  # pure-Python fallback
    BACKEND = "pure-python"

    def levenshtein(a: str, b: str) -> int:
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
            prev = cur
        return prev[-1]

    def ratio(a: str, b: str) -> float:
        total = len(a) + len(b)
        if total == 0:
            return 100.0
        # Same definition rapidfuzz uses: indel-based, 1 - dist/(len a + len b).
        # Indel distance = len(a)+len(b) - 2*LCS.
        m, n = len(a), len(b)
        prev = [0] * (n + 1)
        for i in range(1, m + 1):
            cur = [0] * (n + 1)
            for j in range(1, n + 1):
                cur[j] = prev[j - 1] + 1 if a[i - 1] == b[j - 1] else max(prev[j], cur[j - 1])
            prev = cur
        lcs = prev[n]
        return 100.0 * (2.0 * lcs / total)

    def jaro_winkler(a: str, b: str, p: float = 0.1) -> float:
        if a == b:
            return 1.0
        la, lb = len(a), len(b)
        if not la or not lb:
            return 0.0
        window = max(max(la, lb) // 2 - 1, 0)
        ma, mb = [False] * la, [False] * lb
        matches = 0
        for i, ca in enumerate(a):
            for j in range(max(0, i - window), min(lb, i + window + 1)):
                if not mb[j] and ca == b[j]:
                    ma[i] = mb[j] = True
                    matches += 1
                    break
        if not matches:
            return 0.0
        k = transpositions = 0
        for i in range(la):
            if ma[i]:
                while not mb[k]:
                    k += 1
                if a[i] != b[k]:
                    transpositions += 1
                k += 1
        t = transpositions / 2
        jaro = (matches / la + matches / lb + (matches - t) / matches) / 3
        prefix = 0
        for ca, cb in zip(a[:4], b[:4]):
            if ca != cb:
                break
            prefix += 1
        return jaro + prefix * p * (1 - jaro)

    def token_set_ratio(a: str, b: str) -> float:
        ta, tb = set(a.split()), set(b.split())
        if not ta or not tb:
            return 0.0
        inter = " ".join(sorted(ta & tb))
        diff_a = " ".join(sorted(ta - tb))
        diff_b = " ".join(sorted(tb - ta))
        s1 = inter
        s2 = (inter + " " + diff_a).strip()
        s3 = (inter + " " + diff_b).strip()
        if inter and (not diff_a or not diff_b):
            return 100.0  # one token set is a subset of the other
        return max(ratio(s1, s2), ratio(s1, s3), ratio(s2, s3))
