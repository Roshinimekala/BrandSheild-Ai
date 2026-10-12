import pytest

from app.matcher import compare_names, score_candidate

PROFILE = {
    "name": "Paytm",
    "description": "Paytm - India's leading payments app. Recharge, pay bills, UPI.",
    "official_handles": ["paytm", "paytmcare"],
    "official_app_ids": ["net.one97.paytm", "id473941634"],
    "official_publishers": ["One97 Communications Limited", "Paytm"],
    "keywords": [],
}


@pytest.mark.parametrize(
    "name",
    [
        "Paytrn",            # rn -> m swap
        "Pay tm",            # spacing
        "Pay-tm",            # punctuation
        "Paytm Official Support",  # added trust-bait words
        "Paytm Rewards India",
        "Payt m",
        "Paуtm",             # Cyrillic у
        "P4ytm",             # digit swap
        "Paytmm",            # typo-squat
    ],
)
def test_lookalikes_are_detected(name):
    assert compare_names(name, "Paytm").score >= 0.7, name


@pytest.mark.parametrize(
    "name",
    ["Pay Day Loans", "Palm Tree Cafe", "Amazon", "Phone Tools", "Python Tutorials", "Pytorch"],
)
def test_unrelated_names_not_flagged(name):
    assert compare_names(name, "Paytm").score < 0.7, name


def test_official_social_not_flagged():
    cand = {"kind": "social", "id": "paytm", "handle": "paytm", "name": "Paytm", "source": "mock"}
    assert score_candidate(cand, PROFILE) is None


def test_official_app_not_flagged():
    cand = {
        "kind": "app", "id": "net.one97.paytm", "name": "Paytm: Secure UPI Payments",
        "publisher": "One97 Communications Limited", "source": "mock",
    }
    assert score_candidate(cand, PROFILE) is None


def test_fake_app_is_flagged_with_reasons():
    cand = {
        "kind": "app", "id": "com.fake.paytm", "name": "Paytm Rewards Official",
        "publisher": "Quick Apps Studio",
        "description": "Paytm - India's leading payments app. Recharge, pay bills, UPI.",
        "source": "mock",
    }
    res = score_candidate(cand, PROFILE)
    assert res and res["risk_level"] in {"high", "medium"}
    assert any("publisher" in r.lower() for r in res["reasons"])


def test_fake_social_handle_flagged():
    cand = {
        "kind": "social", "id": "paytm_support_help", "handle": "paytm_support_help",
        "name": "Customer Care", "verified": False, "source": "mock",
    }
    res = score_candidate(cand, PROFILE)
    assert res is not None


def test_benign_not_flagged():
    cand = {"kind": "app", "id": "com.pay.day", "name": "Pay Day Planner",
            "publisher": "Someone", "source": "mock"}
    assert score_candidate(cand, PROFILE) is None
