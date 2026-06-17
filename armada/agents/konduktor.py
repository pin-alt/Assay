"""Konduktor — the orchestrator + report writer.

Runs as a standalone Band agent. Drives the Rondaan Room workflow:
1. @mentions Skaut for discovery
2. Calls the engine tools for screening numbers
3. Writes reports for each company
4. @mentions Pengulas to audit each report
5. Produces a round-up summary
"""

from __future__ import annotations

import asyncio
from typing import Any

from band import Agent

from ..prompts import KONDUKTOR_PROMPT
from ..tools import run_screening, write_report, read_report
from ._common import build_adapter, load_agent_config


async def run_konduktor(agent_id: str, api_key: str) -> None:
    """Run the Konduktor Band agent.

    This blocks until the agent is shut down (Ctrl+C).
    """
    adapter = build_adapter(
        custom_section=KONDUKTOR_PROMPT,
        # Deliberately NO discover_companies: discovery belongs to @Skaut. Without it,
        # Konduktor must @mention Skaut for the candidate list — making the 3-agent
        # handoff real in Band's trail instead of Konduktor self-serving discovery.
        additional_tools=[run_screening, write_report, read_report],
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    print(f"[Konduktor] agent_id={agent_id} — connecting to Band...")
    await agent.run()


def main() -> None:
    """Entry point for `python -m armada.agents.konduktor`."""
    config = load_agent_config()
    konduktor_cfg = config.get("konduktor", config.get("default"))
    if not konduktor_cfg or not konduktor_cfg.get("agent_id"):
        raise RuntimeError(
            "Konduktor credentials not found in agent_config.yaml. "
            "Register the agent at app.band.ai/agents and fill in agent_config.yaml."
        )
    asyncio.run(run_konduktor(konduktor_cfg["agent_id"], konduktor_cfg["api_key"]))


if __name__ == "__main__":
    main()
