"""Deterministic report auditor — the cross-check that makes AUDIT: FAIL code, not judgment.

Every report carries a machine-readable ARMADA-CLAIMS block: the status + ratios the report
asserts. `audit_report()` re-runs the SAME deterministic engine on the source data and diffs
the report's claims against that ground truth. Status, every checked ratio, and the mandatory
disclaimers are verified in pure code. Tamper any asserted number and the verdict flips to
AUDIT: FAIL naming the exact discrepancy, with no model in the loop.

This is the difference from an honesty / provenance audit: we re-derive the number and
compare, so we catch a verdict that is wrong even when the report looks internally honest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .engine import screen_one

# Ratios checked against the engine's latest-year recompute.
CHECKED_RATIOS = ["gearing", "net_margin_pct", "roe_pct", "operating_cashflow_mil"]

# Absolute tolerance. The engine rounds to 1-2 dp and the claims block copies those rounded
# values, so equality is expected; this epsilon only absorbs float representation noise.
_TOL = 0.05

# Strings every compliant report must contain (refusal/compliance discipline).
MANDATORY_STRINGS = ["DISCLAIMER", "SYNTHETIC"]

_CLAIMS_RE = re.compile(r"```armada-claims\s*(\{.*?\})\s*```", re.DOTALL)


def build_claims_block(result: dict, ticker: str) -> str:
    """Produce the canonical ARMADA-CLAIMS block from an engine `screen_one` result.

    Konduktor embeds this in every report; Pengulas re-checks it. INCOMPLETE companies
    carry no ratios (refusal-first).
    """
    ratios: dict = {}
    if result.get("status") in {"PASS", "FAIL"}:
        latest = result["latest_year"]
        r = result["ratios"][latest]
        ratios = {k: r[k] for k in CHECKED_RATIOS}
    claims = {"ticker": ticker, "status": result["status"], "ratios": ratios}
    return "```armada-claims\n" + json.dumps(claims, ensure_ascii=False) + "\n```"


def parse_claims(report_text: str) -> dict | None:
    """Extract and parse the ARMADA-CLAIMS JSON block. None if absent or invalid."""
    m = _CLAIMS_RE.search(report_text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _load_company(data_dir: str, ticker: str) -> dict | None:
    path = Path(data_dir) / f"{ticker}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def audit_report(report_text: str, data_dir: str, ticker: str | None = None) -> dict:
    """Deterministically audit a report against a fresh engine recompute.

    The verdict is a pure function of the report text and the source data; no LLM is
    involved. Returns {"verdict": "AUDIT: PASS"|"AUDIT: FAIL", "ticker",
    "discrepancies": [...], "checks": N}.
    """
    discrepancies: list[str] = []

    claims = parse_claims(report_text)
    if claims is None:
        return {"verdict": "AUDIT: FAIL", "ticker": ticker, "checks": 0,
                "discrepancies": ["no machine-readable ARMADA-CLAIMS block found in report"]}

    ticker = ticker or claims.get("ticker")
    if not ticker:
        return {"verdict": "AUDIT: FAIL", "ticker": None, "checks": 0,
                "discrepancies": ["claims block has no ticker"]}

    data = _load_company(data_dir, ticker)
    if data is None:
        return {"verdict": "AUDIT: FAIL", "ticker": ticker, "checks": 0,
                "discrepancies": [f"source data not found: {ticker}.json"]}

    truth = screen_one(data)
    checks = 0

    # 1. Status must match the engine.
    checks += 1
    claimed_status = claims.get("status")
    if claimed_status != truth["status"]:
        discrepancies.append(
            f"status: report claims {claimed_status!r}, engine says {truth['status']!r}")

    claimed_ratios = claims.get("ratios") or {}

    if truth["status"] in {"PASS", "FAIL"}:
        latest = truth["latest_year"]
        tr = truth["ratios"][latest]
        for k in CHECKED_RATIOS:
            checks += 1
            if k not in claimed_ratios:
                discrepancies.append(f"{k}: missing from report claims (engine={tr[k]})")
                continue
            try:
                cv = float(claimed_ratios[k])
            except (TypeError, ValueError):
                discrepancies.append(f"{k}: report value {claimed_ratios[k]!r} is not a number")
                continue
            if abs(cv - tr[k]) > _TOL:
                discrepancies.append(f"{k}: report claims {cv}, engine computes {tr[k]}")
    else:
        # INCOMPLETE: refusal-first — the report must not assert any ratios.
        checks += 1
        if claimed_ratios:
            discrepancies.append(
                f"status INCOMPLETE but report asserts ratios {sorted(claimed_ratios)} "
                "(refusal-first violated)")

    # 2. Mandatory compliance strings present.
    for s in MANDATORY_STRINGS:
        checks += 1
        if s not in report_text:
            discrepancies.append(f"missing mandatory text: {s}")

    verdict = "AUDIT: PASS" if not discrepancies else "AUDIT: FAIL"
    return {"verdict": verdict, "ticker": ticker, "checks": checks,
            "discrepancies": discrepancies}


def format_verdict(result: dict) -> str:
    """Render the auditor result as the canonical AUDIT block."""
    det = result["discrepancies"]
    return "\n".join([
        result["verdict"],
        f"Ticker: {result['ticker']}",
        f"Checks run: {result['checks']} | Discrepancies: {len(det)}",
        "Details: " + ("; ".join(det) if det else "none"),
    ])


def _main(argv: list[str] | None = None) -> int:
    import sys
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python -m armada.audit <report_path> [data_dir] [ticker]", file=sys.stderr)
        return 2
    report_path = Path(argv[0])
    data_dir = argv[1] if len(argv) > 1 else "data"
    ticker = argv[2] if len(argv) > 2 else None
    if not report_path.exists():
        print(f"AUDIT: FAIL\nreport not found: {report_path}", file=sys.stderr)
        return 1
    result = audit_report(report_path.read_text(encoding="utf-8"), data_dir, ticker)
    print(format_verdict(result))
    return 0 if result["verdict"] == "AUDIT: PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
