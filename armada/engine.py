"""Deterministic screening engine — the ONLY source of financial ratios and status.

Ported from the AVL workshop's screening tool. Pure Python stdlib, no LLM, no
network. Same inputs always produce the same outputs.

Doctrine: numbers come from here, never from an agent's reasoning. Agents call
these functions and report what the code computed; they never compute a ratio.
"""

from __future__ import annotations

import json
from pathlib import Path

COMPANY_FIELDS = ["name", "ticker", "note", "board", "sector", "current_price",
                  "shares_mil", "financials"]
YEAR_FIELDS = ["revenue_mil", "net_profit_mil", "operating_cashflow_mil",
               "total_debt_mil", "equity_mil"]


def _check_fields(data: dict) -> list[str]:
    """Return list of missing fields. Empty list = data complete."""
    missing = [f for f in COMPANY_FIELDS if f not in data]
    financials = data.get("financials", {})
    if "financials" not in missing and len(financials) < 2:
        missing.append("financials (requires at least 2 years of financials)")
    for year, row in sorted(financials.items()):
        for f in YEAR_FIELDS:
            if f not in row:
                missing.append(f"{year}.{f}")
    return missing


def _compute_ratios(row: dict) -> dict:
    """Compute ratios for one financial year. Input must be pre-validated present."""
    profit = row["net_profit_mil"]
    equity = row["equity_mil"]
    return {
        "gearing": round(row["total_debt_mil"] / equity, 2),
        "net_margin_pct": round(100.0 * profit / row["revenue_mil"], 1),
        "roe_pct": round(100.0 * profit / equity, 1),
        "net_profit_mil": profit,
        "operating_cashflow_mil": row["operating_cashflow_mil"],
    }


def screen_one(data: dict) -> dict:
    """Screen one company: PASS / FAIL / INCOMPLETE, with evidence."""
    missing = _check_fields(data)
    if missing:
        # Refusal-first: incomplete data gets NO ratios — only the missing-field list.
        return {
            "name": data.get("name", "(no name)"),
            "status": "INCOMPLETE",
            "missing_fields": missing,
            "reasons": ["incomplete data, screening halted"],
            "ratios": {},
            "criteria": {},
        }

    all_years = sorted(data["financials"])
    latest = all_years[-1]
    ratios = {y: _compute_ratios(data["financials"][y]) for y in all_years}
    r = ratios[latest]

    profit_positive_all = all(ratios[y]["net_profit_mil"] > 0 for y in all_years)
    criteria = {
        "K1_gearing": {"value": r["gearing"], "limit": "< 1.0", "passed": r["gearing"] < 1.0},
        "K2_net_margin_pct": {"value": r["net_margin_pct"], "limit": "> 5.0",
                              "passed": r["net_margin_pct"] > 5.0},
        "K3_roe_pct": {"value": r["roe_pct"], "limit": "> 8.0", "passed": r["roe_pct"] > 8.0},
        "K4_profit_positive_all_years": {
            "value": {y: ratios[y]["net_profit_mil"] for y in all_years},
            "limit": "> 0 each year", "passed": profit_positive_all},
        "K5_latest_ocf_positive": {
            "value": r["operating_cashflow_mil"], "limit": "> 0",
            "passed": r["operating_cashflow_mil"] > 0},
    }

    failed = [k for k, v in criteria.items() if not v["passed"]]
    if failed:
        reasons = [f"{k}: value {criteria[k]['value']} (limit {criteria[k]['limit']})" for k in failed]
        status = "FAIL"
    else:
        reasons = ["all 5 criteria passed"]
        status = "PASS"

    return {
        "name": data["name"], "status": status, "missing_fields": [], "reasons": reasons,
        "latest_year": latest, "ratios": ratios, "criteria": criteria,
    }


def screen_all(data_dir: Path) -> dict[str, dict]:
    """Screen every *.json in data_dir. Returns {ticker: result}."""
    results: dict[str, dict] = {}
    for path in sorted(data_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        ticker = data.get("ticker", path.stem)
        results[ticker] = screen_one(data)
    return results


def list_companies(data_dir: Path) -> list[dict]:
    """Lightweight company index for discovery (no ratios computed)."""
    companies = []
    for path in sorted(data_dir.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        companies.append({
            "ticker": d.get("ticker", path.stem),
            "name": d.get("name", ""),
            "board": d.get("board", ""),
            "sector": d.get("sector", ""),
            "note": d.get("note", ""),
            "file": path.name,
        })
    return companies
