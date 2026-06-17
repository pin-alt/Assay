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
from band.core.types import AdapterFeatures, Emit

# Load .env once at module level
_load_env = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_load_env)


def _build_llm() -> Any:
    """Build the LLM from environment variables, selected by MODEL_PROVIDER.

    MODEL_PROVIDER (default "glm") picks the brain. All but Claude are
    OpenAI-compatible and share one ChatOpenAI factory:

        glm         GLM-5.2 via z.ai          (free dev default)
        aimlapi     AI/ML API gateway          (partner prize lane; route a
                                                frontier tool-caller for the
                                                recorded demo)
        featherless Featherless serverless OSS (partner prize lane; Qwen3
                                                family supports tool-calling)
        claude      Anthropic direct           (break-glass max reliability;
                                                needs `uv add langchain-anthropic`)

    Flip one env var to swap brains mid-demo — no code edit.
    """
    provider = os.getenv("MODEL_PROVIDER", "glm").strip().lower()

    if provider == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "MODEL_PROVIDER=claude but ANTHROPIC_API_KEY not set in .env."
            )
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise RuntimeError(
                "MODEL_PROVIDER=claude needs langchain-anthropic. "
                "Run: uv add langchain-anthropic"
            ) from exc
        model = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")
        return ChatAnthropic(model=model, api_key=api_key, temperature=0.1)

    # OpenAI-compatible providers: (key env var, base_url default, model default)
    presets = {
        "glm": (
            "GLM_API_KEY",
            os.getenv("GLM_BASE_URL", "https://api.z.ai/api/paas/v4/"),
            os.getenv("GLM_MODEL", "glm-5.2"),
        ),
        "aimlapi": (
            "AIMLAPI_API_KEY",
            os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1"),
            os.getenv("AIMLAPI_MODEL", "gpt-4o"),
        ),
        "featherless": (
            "FEATHERLESS_API_KEY",
            os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
            os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen3-235B-A22B"),
        ),
    }
    if provider not in presets:
        raise RuntimeError(
            f"Unknown MODEL_PROVIDER={provider!r}. "
            "Use one of: glm | aimlapi | featherless | claude."
        )

    key_env, base_url, model = presets[provider]
    api_key = os.getenv(key_env)
    if not api_key:
        raise RuntimeError(
            f"MODEL_PROVIDER={provider} but {key_env} not set. "
            "Add it to .env (see .env.example)."
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
        # Without EXECUTION emit, tool_call/tool_result events are NOT sent to Band's
        # audit trail (gated in adapters/langgraph.py). That trail is the hackathon
        # win-gate; default features leave emit empty, so request it explicitly.
        features=AdapterFeatures(emit={Emit.EXECUTION}),
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
