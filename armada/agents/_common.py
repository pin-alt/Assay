"""Shared LLM + LangGraphAdapter factory for all three Armada agents.

Each agent gets its own adapter instance, so prompts and tools can differ.
Primary: GLM-5.2 via z.ai OpenAI-compatible endpoint (zero cost, user's brain).
Fallback: swap to Claude by setting ANTHROPIC_API_KEY and changing the model factory.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from band import Agent
from band.adapters.langgraph import LangGraphAdapter

# Load .env once at module level
_load_env = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_load_env)


def _build_llm() -> ChatOpenAI:
    """Build the LLM from environment variables.

    Primary: GLM-5.2 via z.ai (GLM_API_KEY, GLM_MODEL, GLM_BASE_URL).
    Fallback: set ANTHROPIC_API_KEY and change the model to claude via config.
    """
    api_key = os.getenv("GLM_API_KEY")
    model = os.getenv("GLM_MODEL", "glm-5.2")
    base_url = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")

    if not api_key:
        raise RuntimeError(
            "GLM_API_KEY not set. Create a .env file from .env.example "
            "with your z.ai API key."
        )

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0.1,
    )


def build_adapter(
    custom_section: str,
    additional_tools: list[Any] | None = None,
) -> LangGraphAdapter:
    """Build a LangGraphAdapter for one agent.

    Args:
        custom_section: The agent's system prompt (from prompts.py).
        additional_tools: Custom tools for this agent (from tools.py).
            Different agents get different tools:
            - Skaut: discover_companies, screen_one_company
            - Konduktor: all tools
            - Pengulas: screen_one_company, run_screening, read_report
    """
    return LangGraphAdapter(
        llm=_build_llm(),
        checkpointer=InMemorySaver(),
        custom_section=custom_section,
        additional_tools=additional_tools or [],
    )


def load_agent_config() -> dict[str, dict[str, str]]:
    """Load Band platform credentials from agent_config.yaml.

    Returns {agent_name: {agent_id, api_key}} for skaut, konduktor, pengulas.
    Falls back to environment variables BAND_AGENT_ID / BAND_API_KEY if the
    config file is missing (single-agent demo mode).
    """
    import yaml

    config_path = Path("agent_config.yaml")
    if not config_path.exists():
        agent_id = os.getenv("BAND_AGENT_ID", "")
        api_key = os.getenv("BAND_API_KEY", "")
        if agent_id and api_key:
            return {
                "default": {"agent_id": agent_id, "api_key": api_key},
            }
        raise RuntimeError(
            "agent_config.yaml not found and BAND_AGENT_ID/BAND_API_KEY not set. "
            "Copy agent_config.yaml.example to agent_config.yaml and fill in "
            "your Band agent credentials from app.band.ai/agents."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
