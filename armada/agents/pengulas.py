"""Pengulas — the cross-auditor.

Runs as a standalone Band agent. When @mentioned by Konduktor, it re-runs the
deterministic engine to verify every number in a report. Reports AUDIT: PASS
or AUDIT: FAIL with specific discrepancies.
"""

from __future__ import annotations

import asyncio
from typing import Any

from band import Agent

from ..prompts import PENGULAS_PROMPT
from ..tools import screen_one_company, run_screening, read_report, audit_report
from ._common import build_adapter, load_agent_config


async def run_pengulas(agent_id: str, api_key: str) -> None:
    """Run the Pengulas Band agent.

    This blocks until the agent is shut down (Ctrl+C).
    """
    adapter = build_adapter(
        custom_section=PENGULAS_PROMPT,
        additional_tools=[screen_one_company, run_screening, read_report, audit_report],
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    print(f"[Pengulas] agent_id={agent_id} — connecting to Band...")
    await agent.run()


def main() -> None:
    """Entry point for `python -m armada.agents.pengulas`."""
    config = load_agent_config()
    pengulas_cfg = config.get("pengulas", config.get("default"))
    if not pengulas_cfg or not pengulas_cfg.get("agent_id"):
        raise RuntimeError(
            "Pengulas credentials not found in agent_config.yaml. "
            "Register the agent at app.band.ai/agents and fill in agent_config.yaml."
        )
    asyncio.run(run_pengulas(pengulas_cfg["agent_id"], pengulas_cfg["api_key"]))


if __name__ == "__main__":
    main()
