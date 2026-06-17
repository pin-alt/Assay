"""Tool wrappers: correct shapes, deterministic delegation to engine."""
import json
from pathlib import Path

from armada.tools import (
    run_screening,
    screen_one_company,
    discover_companies,
    write_report,
    read_report,
)

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = Path(__file__).resolve().parent.parent / "output"


def test_run_screening_returns_json_string():
    raw = run_screening.invoke({"data_dir": str(DATA)})
    parsed = json.loads(raw)
    assert "ORKES-A" in parsed
    assert parsed["ORKES-A"]["status"] == "PASS"


def test_discover_companies_returns_list():
    raw = discover_companies.invoke({"data_dir": str(DATA)})
    parsed = json.loads(raw)
    assert len(parsed) == 6
    assert parsed[0]["ticker"] == "ORKES-A"


def test_screen_one_company_known_pass():
    raw = screen_one_company.invoke({"data_dir": str(DATA), "ticker": "ORKES-A"})
    parsed = json.loads(raw)
    assert parsed["status"] == "PASS"
    assert parsed["criteria"]["K1_gearing"]["passed"] is True


def test_screen_one_company_known_fail():
    raw = screen_one_company.invoke({"data_dir": str(DATA), "ticker": "ORKES-B"})
    parsed = json.loads(raw)
    assert parsed["status"] == "FAIL"


def test_screen_one_company_not_found():
    raw = screen_one_company.invoke({"data_dir": str(DATA), "ticker": "NONEXIST"})
    parsed = json.loads(raw)
    assert "error" in parsed


def test_write_and_read_report():
    OUT.mkdir(exist_ok=True)
    # Write
    result = write_report.invoke({"path": "test_report.md", "content": "# Test\nHello"})
    assert "test_report.md" in result
    # Read back
    content = read_report.invoke({"path": "test_report.md"})
    assert "Hello" in content
    # Cleanup
    (OUT / "test_report.md").unlink(missing_ok=True)


def test_read_report_tolerates_output_prefix():
    """Passing an 'output/'-prefixed path must resolve to output/X, not output/output/X."""
    OUT.mkdir(exist_ok=True)
    write_report.invoke({"path": "prefix_test.md", "content": "# X\nWorld"})
    content = read_report.invoke({"path": "output/prefix_test.md"})
    assert "World" in content
    (OUT / "prefix_test.md").unlink(missing_ok=True)


def test_all_tools_in_registry():
    from armada.tools import ALL_TOOLS
    assert len(ALL_TOOLS) == 5
    names = {t.name for t in ALL_TOOLS}
    assert names == {"run_screening", "screen_one_company", "discover_companies",
                     "write_report", "read_report"}
