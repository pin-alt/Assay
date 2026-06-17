"""Deterministic engine: same inputs -> same outputs, always. No LLM, no network."""
import json
from pathlib import Path

from armada.engine import screen_all, screen_one, list_companies

DATA = Path(__file__).resolve().parent.parent / "data"

EXPECTED_STATUS = {
    "ORKES-A": "PASS",
    "ORKES-B": "FAIL",
    "ORKES-C": "FAIL",
    "ORKES-D": "INCOMPLETE",
    "ORKES-E": "PASS",
    "ORKES-F": "INCOMPLETE",
}


def test_screen_all_returns_every_company():
    results = screen_all(DATA)
    assert set(results.keys()) == set(EXPECTED_STATUS.keys())


def test_screen_all_statuses_match_oracle():
    results = screen_all(DATA)
    for ticker, expected in EXPECTED_STATUS.items():
        assert results[ticker]["status"] == expected, (
            f"{ticker}: expected {expected}, got {results[ticker]['status']}"
        )


def test_orkes_b_fails_gearing_only():
    r = screen_one(json.loads((DATA / "ORKES-B.json").read_text(encoding="utf-8")))
    crit = r["criteria"]
    assert not crit["K1_gearing"]["passed"]
    assert all(crit[k]["passed"] for k in crit if k != "K1_gearing")


def test_orkes_d_missing_fields_identified():
    r = screen_one(json.loads((DATA / "ORKES-D.json").read_text(encoding="utf-8")))
    assert "sector" in r["missing_fields"]
    assert "FY2025.operating_cashflow_mil" in r["missing_fields"]


def test_incomplete_company_has_no_ratios():
    """Refusal-first: incomplete data gets NO computed ratios, only the missing-field list."""
    r = screen_one(json.loads((DATA / "ORKES-D.json").read_text(encoding="utf-8")))
    assert r["ratios"] == {}
    assert r["criteria"] == {}


def test_list_companies_returns_tickers():
    companies = list_companies(DATA)
    assert {"ticker", "name", "board", "sector"} <= set(companies[0].keys())
    assert len(companies) == 6
