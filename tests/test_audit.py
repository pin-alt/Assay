"""Tamper test: the deterministic auditor catches a doctored report, in code.

This is the proof behind the "we catch wrong-but-honest" claim. The auditor re-runs the
engine and diffs the report's asserted numbers; no LLM is involved, so these assertions are
the same offline as on stage.
"""

from __future__ import annotations

import json
from pathlib import Path

from armada.audit import audit_report, build_claims_block, parse_claims
from armada.engine import screen_one

DATA = str(Path(__file__).resolve().parents[1] / "data")

DISCLAIMER = ("---\nDISCLAIMER: educational screening tool, not investment advice. "
              "Data status: SYNTHETIC.\n")


def _truth(ticker: str) -> dict:
    data = json.loads((Path(DATA) / f"{ticker}.json").read_text(encoding="utf-8"))
    return screen_one(data)


def _report_from_claims(claims: dict) -> str:
    """Build a minimal but compliant report wrapping an arbitrary claims dict."""
    block = "```armada-claims\n" + json.dumps(claims, ensure_ascii=False) + "\n```"
    return f"# Screening Report: {claims.get('ticker')}\n\n{block}\n\n{DISCLAIMER}"


def _clean_report(ticker: str) -> str:
    """A faithful report whose claims match the engine exactly."""
    truth = _truth(ticker)
    block = build_claims_block(truth, ticker)
    return f"# Screening Report: {ticker}\n\n{block}\n\n{DISCLAIMER}"


# --- Clean reports pass -----------------------------------------------------

def test_clean_pass_report_audits_pass():
    res = audit_report(_clean_report("ORKES-A"), DATA)
    assert res["verdict"] == "AUDIT: PASS", res["discrepancies"]
    assert res["discrepancies"] == []


def test_clean_fail_report_audits_pass():
    # A faithfully-reported FAIL company is itself a correct report -> PASS audit.
    assert _truth("ORKES-B")["status"] == "FAIL"
    res = audit_report(_clean_report("ORKES-B"), DATA)
    assert res["verdict"] == "AUDIT: PASS", res["discrepancies"]


# --- Tampered numbers are caught -------------------------------------------

def test_doctored_ratio_audits_fail():
    claims = parse_claims(_clean_report("ORKES-A"))
    claims["ratios"]["gearing"] = claims["ratios"]["gearing"] + 99.0  # doctor one number
    res = audit_report(_report_from_claims(claims), DATA)
    assert res["verdict"] == "AUDIT: FAIL"
    assert any("gearing" in d for d in res["discrepancies"])


def test_doctored_status_audits_fail():
    claims = parse_claims(_clean_report("ORKES-A"))
    assert claims["status"] == "PASS"
    claims["status"] = "FAIL"  # flip the verdict, keep honest-looking ratios
    res = audit_report(_report_from_claims(claims), DATA)
    assert res["verdict"] == "AUDIT: FAIL"
    assert any("status" in d for d in res["discrepancies"])


def test_wrong_but_honest_is_caught():
    """Ratios internally consistent and plausible, but not what the engine computes."""
    claims = {"ticker": "ORKES-A", "status": "PASS",
              "ratios": {"gearing": 0.10, "net_margin_pct": 40.0,
                         "roe_pct": 35.0, "operating_cashflow_mil": 999.0}}
    res = audit_report(_report_from_claims(claims), DATA)
    assert res["verdict"] == "AUDIT: FAIL"
    assert len(res["discrepancies"]) >= 1


# --- Structural / compliance failures --------------------------------------

def test_missing_claims_block_audits_fail():
    res = audit_report("# Report with prose only, no machine block\n" + DISCLAIMER, DATA, "ORKES-A")
    assert res["verdict"] == "AUDIT: FAIL"
    assert any("ARMADA-CLAIMS" in d for d in res["discrepancies"])


def test_missing_disclaimer_audits_fail():
    truth = _truth("ORKES-A")
    block = build_claims_block(truth, "ORKES-A")
    report = f"# Report without disclaimer\n\n{block}\n"  # no DISCLAIMER / SYNTHETIC
    res = audit_report(report, DATA)
    assert res["verdict"] == "AUDIT: FAIL"
    assert any("DISCLAIMER" in d for d in res["discrepancies"])


def test_unknown_ticker_audits_fail():
    claims = {"ticker": "ORKES-NOPE", "status": "PASS", "ratios": {}}
    res = audit_report(_report_from_claims(claims), DATA)
    assert res["verdict"] == "AUDIT: FAIL"
    assert any("not found" in d for d in res["discrepancies"])


# --- Refusal-first on INCOMPLETE -------------------------------------------

def test_incomplete_clean_report_audits_pass():
    assert _truth("ORKES-D")["status"] == "INCOMPLETE"
    res = audit_report(_clean_report("ORKES-D"), DATA)
    assert res["verdict"] == "AUDIT: PASS", res["discrepancies"]


def test_incomplete_with_asserted_ratios_audits_fail():
    claims = {"ticker": "ORKES-D", "status": "INCOMPLETE",
              "ratios": {"gearing": 0.5}}  # asserting numbers it must refuse to compute
    res = audit_report(_report_from_claims(claims), DATA)
    assert res["verdict"] == "AUDIT: FAIL"
    assert any("refusal-first" in d for d in res["discrepancies"])
