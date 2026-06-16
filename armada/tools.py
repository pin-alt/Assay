"""LangChain tools wrapping the deterministic screening engine.

These are the ONLY path through which agents touch financial numbers. Every tool
delegates to the engine; no agent computes a ratio.

Tool contract:
- `run_screening(data_dir)` -> JSON string of {ticker: screen_one_result}
- `discover_companies(data_dir)` -> JSON string of [{ticker, nama, papan, sektor, nota, fail}]
- `read_report(report_path)` -> str (file contents)
- `write_report(report_path, content)` -> str (confirmation)
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool

from .engine import screen_all, screen_one, list_companies


@tool
def run_screening(data_dir: str) -> str:
    """Screen every company in data_dir/*.json.

    Returns JSON: {ticker: {nama, status (LULUS/GAGAL/TIDAK LENGKAP), sebab, kriteria, nisbah, medan_hilang}}.
    This is the ONLY source of financial ratios and screening status. NEVER compute a ratio yourself.
    """
    results = screen_all(Path(data_dir))
    return json.dumps(results, ensure_ascii=False, indent=2)


@tool
def screen_one_company(data_dir: str, ticker: str) -> str:
    """Screen ONE specific company by its ticker (e.g., ORKES-A).

    Returns JSON with full screening result: {nama, status, sebab, kriteria, nisbah}.
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

    Returns JSON array: [{ticker, nama, papan, sektor, nota, fail}].
    """
    companies = list_companies(Path(data_dir))
    return json.dumps(companies, ensure_ascii=False, indent=2)


@tool
def write_report(path: str, content: str) -> str:
    """Write a report file. Call only with final, verified content.

    Args:
        path: Path relative to output/ (e.g., 'Laporan_ORKES-A.md')
        content: The complete markdown report text
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / path
    report_path.write_text(content, encoding="utf-8")
    return f"Report written to output/{path}"


@tool
def read_report(path: str) -> str:
    """Read a previously written report file.

    Args:
        path: Path relative to output/ (e.g., 'Laporan_ORKES-A.md')
    """
    report_path = Path("output") / path
    if not report_path.exists():
        return f"Report not found: output/{path}"
    return report_path.read_text(encoding="utf-8")


# Registry for the LangGraphAdapter additional_tools
ALL_TOOLS = [run_screening, screen_one_company, discover_companies, write_report, read_report]
