"""LangChain tools wrapping the deterministic screening engine.

These are the ONLY path through which agents touch financial numbers. Every tool
delegates to the engine; no agent computes a ratio.

Tool contract:
- run_screening(data_dir)              -> JSON string of {ticker: screen_one result}
- screen_one_company(data_dir, ticker) -> JSON string of one screen result
- discover_companies(data_dir)         -> JSON string of [{ticker, name, board, sector, note, file}]
- read_report(path)                    -> str (file contents)
- write_report(path, content)          -> str (confirmation)
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool

from .audit import audit_report as _audit_report, format_verdict
from .engine import screen_all, screen_one, list_companies


def _output_path(path: str) -> Path:
    """Resolve a report path under output/, tolerating an 'output/' prefix.

    Agents pass 'Report_X.md' sometimes and 'output/Report_X.md' other times
    (the Konduktor prompt uses the prefixed form when handing off to Pengulas).
    Both must resolve to output/Report_X.md — never output/output/Report_X.md,
    which would cause a spurious 'report not found' / false AUDIT: FAIL.
    """
    p = Path(path)
    if p.parts and p.parts[0] == "output" and len(p.parts) > 1:
        p = Path(*p.parts[1:])
    return Path("output") / p


@tool
def run_screening(data_dir: str) -> str:
    """Screen every company in data_dir/*.json.

    Returns JSON: {ticker: {name, status (PASS/FAIL/INCOMPLETE), reasons, criteria, ratios, missing_fields}}.
    This is the ONLY source of financial ratios and screening status. NEVER compute a ratio yourself.
    """
    results = screen_all(Path(data_dir))
    return json.dumps(results, ensure_ascii=False, indent=2)


@tool
def screen_one_company(data_dir: str, ticker: str) -> str:
    """Screen ONE specific company by its ticker (e.g., ORKES-A).

    Returns JSON with the full screening result: {name, status, reasons, criteria, ratios}.
    Use this when cross-auditing a specific report.
    """
    path = Path(data_dir) / f"{ticker}.json"
    if not path.exists():
        return json.dumps({"error": f"Company file not found: {ticker}.json"})
    data = json.loads(path.read_text(encoding="utf-8"))
    result = screen_one(data)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def discover_companies(data_dir: str) -> str:
    """List all companies available for screening (no ratios computed).

    Returns JSON array: [{ticker, name, board, sector, note, file}].
    """
    companies = list_companies(Path(data_dir))
    return json.dumps(companies, ensure_ascii=False, indent=2)


@tool
def write_report(path: str, content: str) -> str:
    """Write a report file. Call only with final, verified content.

    Args:
        path: Filename under output/ (e.g., 'Report_ORKES-A.md')
        content: The complete markdown report text
    """
    Path("output").mkdir(exist_ok=True)
    report_path = _output_path(path)
    report_path.write_text(content, encoding="utf-8")
    return f"Report written to {report_path.as_posix()}"


@tool
def read_report(path: str) -> str:
    """Read a previously written report file.

    Args:
        path: Filename under output/ (e.g., 'Report_ORKES-A.md')
    """
    report_path = _output_path(path)
    if not report_path.exists():
        return f"Report not found: {report_path.as_posix()}"
    return report_path.read_text(encoding="utf-8")


@tool
def audit_report(report_path: str, data_dir: str) -> str:
    """Deterministically audit a written report against a fresh engine recompute.

    Re-runs the screening engine on the source data and diffs the report's ARMADA-CLAIMS
    block (status + ratios) plus the mandatory disclaimers. Returns the canonical
    AUDIT: PASS / AUDIT: FAIL block with exact discrepancies. The verdict is computed in
    code, not judged by you: call this and report its output VERBATIM.

    Args:
        report_path: Filename under output/ (e.g., 'Report_ORKES-A.md')
        data_dir: The data folder holding the source company JSON (e.g., 'data')
    """
    p = _output_path(report_path)
    if not p.exists():
        return f"AUDIT: FAIL\nreport not found: {p.as_posix()}"
    result = _audit_report(p.read_text(encoding="utf-8"), data_dir)
    return format_verdict(result)


# Registry for the LangGraphAdapter additional_tools
ALL_TOOLS = [run_screening, screen_one_company, discover_companies, write_report,
             read_report, audit_report]
