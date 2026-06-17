"""Assay — launch one or all screening agents.

Usage:
    # Launch all three agents (requires 3 terminals or background)
    uv run python -m armada.runner --all

    # Launch one agent
    uv run python -m armada.runner --skaut
    uv run python -m armada.runner --konduktor
    uv run python -m armada.runner --pengulas

    # Demo mode: run the engine directly (no Band platform needed)
    uv run python -m armada.runner --demo
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from armada.engine import screen_all
from armada.agents._common import load_agent_config
from armada.agents.skaut import run_skaut
from armada.agents.konduktor import run_konduktor
from armada.agents.pengulas import run_pengulas


async def _run_all() -> None:
    """Launch all three agents as concurrent tasks."""
    config = load_agent_config()
    tasks = []

    for name, runner in [
        ("skaut", run_skaut),
        ("konduktor", run_konduktor),
        ("pengulas", run_pengulas),
    ]:
        cfg = config.get(name)
        if not cfg or not cfg.get("agent_id"):
            print(f"[!] Missing {name} credentials — skipping")
            continue
        print(f"[+] Starting {name} (agent_id={cfg['agent_id']})")
        tasks.append(runner(cfg["agent_id"], cfg["api_key"]))

    if not tasks:
        print("No agents configured. Fill in agent_config.yaml from agent_config.yaml.example.")
        return

    await asyncio.gather(*tasks)


def _demo() -> None:
    """Run the engine directly — no Band platform, no LLM, just the engine."""
    print("=" * 70)
    print("  BAND ARMADA — Demo (engine only, no Band platform)")
    print("=" * 70)

    data_dir = Path("data")
    if not data_dir.exists():
        print(f"ERROR: data/ directory not found at {data_dir.absolute()}")
        sys.exit(1)

    results = screen_all(data_dir)

    print(f"\n{'TICKER':10} {'STATUS':15} DETAILS")
    print("-" * 70)
    for ticker, r in sorted(results.items()):
        if r["status"] == "INCOMPLETE":
            detail = "missing: " + ", ".join(r["missing_fields"])
        else:
            detail = "; ".join(r["reasons"])
        print(f"{ticker:10} {r['status']:15} {detail}")

    print("-" * 70)

    # Counts
    counts = {"PASS": 0, "FAIL": 0, "INCOMPLETE": 0}
    for r in results.values():
        counts[r["status"]] += 1

    print(f"PASS: {counts['PASS']}  |  FAIL: {counts['FAIL']}  |  INCOMPLETE: {counts['INCOMPLETE']}")
    print("\nTheory: every ratio above was computed by Python stdlib, not an LLM.")
    print("For the full multi-agent experience: register agents at app.band.ai/agents,")
    print("fill in agent_config.yaml, and run 'uv run python -m armada.runner --all'.")


def main() -> None:
    if "--demo" in sys.argv:
        _demo()
    elif "--all" in sys.argv:
        asyncio.run(_run_all())
    elif "--skaut" in sys.argv:
        config = load_agent_config()
        cfg = config.get("skaut", config.get("default"))
        asyncio.run(run_skaut(cfg["agent_id"], cfg["api_key"]))
    elif "--konduktor" in sys.argv:
        config = load_agent_config()
        cfg = config.get("konduktor", config.get("default"))
        asyncio.run(run_konduktor(cfg["agent_id"], cfg["api_key"]))
    elif "--pengulas" in sys.argv:
        config = load_agent_config()
        cfg = config.get("pengulas", config.get("default"))
        asyncio.run(run_pengulas(cfg["agent_id"], cfg["api_key"]))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
