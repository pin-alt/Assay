"""Skaut — the discovery agent.

Runs as a standalone Band agent. When @mentioned by Konduktor in the Rondaan
Room, it inspects the data folder and reports candidates with completeness notes.
"""

from __future__ import annotations

import asyncio
from typing import Any

from band import Agent

from ..prompts import SKAUT_PROMPT
from ..tools import discover_companies, screen_one_company
from ._common import build_adapter, load_agent_config


async def run_skaut(agent_id: str, api_key: str) -> None:
    """Run the Skaut Band agent.

    This blocks until the agent is shut down (Ctrl+C).
    """
    adapter = build_adapter(
        custom_section=SKAUT_PROMPT,
        additional_tools=[discover_companies, screen_one_company],
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    print(f"[Skaut] agent_id={agent_id} — connecting to Band...")
    await agent.run()


def main() -> None:
    """Entry point for `python -m armada.agents.skaut`."""
    config = load_agent_config()
    skaut_cfg = config.get("skaut", config.get("default"))
    if not skaut_cfg or not skaut_cfg.get("agent_id"):
        raise RuntimeError(
            "Skaut credentials not found in agent_config.yaml. "
            "Register the agent at app.band.ai/agents and fill in agent_config.yaml."
        )
    asyncio.run(run_skaut(skaut_cfg["agent_id"], skaut_cfg["api_key"]))


if __name__ == "__main__":
    main()
