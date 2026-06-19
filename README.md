# Assay — Multi-Agent Investment Screening Desk

**Nombor dari kod. AI mengarah, kod mengira, manusia memutuskan.**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://althea.streamlit.app/)

**Live demo:** the [Audit Bench](https://althea.streamlit.app/) lets you tamper a figure and watch the deterministic auditor flip the verdict to FAIL, with the engine formula shown in-app. The full three-agent Band run is in the demo video and RUNBOOK.md.

A Band-native multi-agent system where three AI agents collaborate through
@mention chat rooms to screen stocks — but every financial number comes from
a deterministic Python engine, and a separate agent cross-audits every report.

**Hackathon:** Band of Agents (lablab.ai), June 12–19, 2026  
**Status:** Engine + deterministic auditor + 24/24 tests ✅ | Band agents validated live on Claude + GLM-5.2 ✅

---

## How it works

```
User ──@Konduktor──►  RONDAAN ROOM (Band chat)
  "run rondaan"
                       ┌──────────┐  @Skaut  ┌──────────┐
                       │ Konduktor │─────────►│  Skaut   │
                       │(orchestr.)│◄─cand.──│(discover)│
                       │           │          └──────────┘
                       │    │ calls run_screening TOOL
                       │    ▼      │
                       │ [ENGINE]  │ ◄── deterministic Python
                       │    │      │
                       │  writes   │  @Pengulas  ┌──────────┐
                       │  reports  │────────────►│ Pengulas  │
                       └───────────┘◄──AUDIT:OK──│ (auditor) │
                                                  └──────────┘
```

**The engine is the single source of truth.** No agent computes a ratio.
The Konduktor calls the engine, writes reports, then Pengulas re-runs the
engine to cross-audit every number. Numbers that can't be traced back = audit
failure. This is the "grounded agent" posture Band's own marketing sells.

---

## Quick start

### 1. Engine only (no Band platform, no LLM)

```bash
cd D:\02-Projects\2026-06-16-band-armada
uv sync --extra dev
uv run python -m armada.runner --demo
```

Output: all 6 synthetic companies screened in <1 second. PASS: 2, FAIL: 2,
INCOMPLETE: 2.

### 2. Run tests

```bash
uv run pytest -v                          # 24 tests, all pass
```

### 3. Launch on Band platform (needs registered agents)

```bash
# 1. Register 3 agents at app.band.ai/agents
# 2. Copy credentials
cp agent_config.yaml.example agent_config.yaml
# Fill in each agent's agent_id + api_key

# 3. Create .env
cp .env.example .env
# Fill in GLM_API_KEY (z.ai)

# 4. Launch all three agents (separate terminals or background)
uv run python -m armada.runner --skaut      # terminal 1
uv run python -m armada.runner --konduktor   # terminal 2
uv run python -m armada.runner --pengulas    # terminal 3

# Or all at once:
uv run python -m armada.runner --all
```

Then in the Band app, @mention Konduktor with "run rondaan" and watch the
orchestra play.

---

## Project layout

```
2026-06-16-band-armada/
├── armada/
│   ├── engine.py         # Deterministic screening (verbatim AVL port)
│   ├── tools.py          # LangChain @tools wrapping the engine
│   ├── prompts.py        # Agent system prompts (ported from AVL CLAUDE.md)
│   ├── runner.py         # CLI entry point
│   └── agents/
│       ├── _common.py    # Shared LLM + LangGraphAdapter factory
│       ├── skaut.py      # Discovery agent
│       ├── konduktor.py  # Orchestrator + report writer
│       └── pengulas.py   # Cross-auditor
├── data/                 # 6 synthetic companies (ORKES-A..F.json)
├── output/               # Reports land here
└── tests/
    ├── test_engine.py    # 6 tests: all statuses match oracle
    ├── test_tools.py     # 8 tests: tool shapes + read/write cycle
    └── test_audit.py     # 10 tests: tamper test, deterministic correctness audit
```

---

## The doctrine (why this wins)

Most hackathon entries will have agents that happily invent numbers. This
submission has agents that **architecturally refuse to compute:**

| Guardrail | How |
|---|---|
| Numbers from code | All ratios come from `armada/engine.py` — Python stdlib |
| Agents can't compute | Tools are read-only wrappers; no agent has ratio logic |
| Cross-audit | Separate Pengulas agent re-runs the engine to verify reports |
| Refusal-first | Incomplete data = INCOMPLETE, no ratios, no report |
| Full audit trail | Band platform captures every message + tool call |
| Zero hallucination surface | The LLM directs, explains, and audits — never calculates |

---

## Correctness audit (the wedge)

Most governed-agent systems audit whether the AI was *honest* about its number (does the
claim cite evidence? was the transcript tampered?). Assay audits whether the number is
*right*. Every report carries a machine-readable `armada-claims` block; the auditor re-runs
the deterministic engine on the source data and diffs the claims in pure code. The verdict is
not a model judgment, so it catches a report that is wrong even when it looks internally
honest.

```bash
# Audit any report against a fresh engine recompute (no LLM, no Band needed)
uv run python -m armada.audit output/Report_ORKES-A.md data ORKES-A
# -> AUDIT: PASS   (clean report)
# Doctor one ratio in the report, run it again:
# -> AUDIT: FAIL   Details: gearing: report claims 0.01, engine computes 0.26
```

A SHA-256 hash proves nobody altered a report; it does not prove the report is right. We
prove it by recomputing it. The tamper test (`tests/test_audit.py`) is this guarantee, green
offline.

## Portable correctness — model- and framework-agnostic

The verdict is a pure function of the report text plus the source data, computed in
`armada/audit.py` with **no model in the loop**. So correctness is independent of the brain:
swap `MODEL_PROVIDER` between `claude` (Anthropic) and `glm` (z.ai / GLM-5.2),
or any OpenAI-compatible endpoint, by one env var (no code edit), and the AUDIT
verdict is byte-identical, because no model ever touches a number.

| Brain (provider) | Drives the Band tool loop | AUDIT verdict (deterministic) |
|---|---|---|
| Claude (Anthropic) | validated live through Band | 4 PASS · 2 refused |
| GLM-5.2 (z.ai) | validated live through Band | 4 PASS · 2 refused |
| Any OpenAI-compatible brain | swap by one env var | identical by construction |

Per-brain captures land in `hackathon/evidence/BRAINS.md`. The verdict column is identical
*by construction*: `tests/test_audit.py` proves `audit_report()` is a pure function of report +
data, so changing the brain cannot change it.

The audit layer is **framework-agnostic** too: the `armada-claims` block is plain JSON and
`audit_report()` is pure-Python with zero agent-framework deps. Any stack that emits the claims
block — LangGraph here, but equally CrewAI, AutoGen, or raw OpenAI calls — can be audited by the
same neutral recompute. The correctness control is portable across both the model and the
framework: an enterprise governance buyer can swap either without re-validating the control.

## The numbers

```
ORKES-A  PASS        All 5 criteria pass
ORKES-B  FAIL        K1_gearing: 1.52 (limit < 1.0)
ORKES-C  FAIL        K2_net_margin_pct: 1.5 (limit > 5.0); K3_roe_pct: 3.6 (limit > 8.0)
ORKES-D  INCOMPLETE  Missing: sector, FY2025.operating_cashflow_mil
ORKES-E  PASS        All 5 criteria pass
ORKES-F  INCOMPLETE  Missing: financials (requires at least 2 years of financials)
```

---

## Model

Primary: **Claude** (Anthropic), validated live through Band. Backup: **GLM-5.2** via z.ai
OpenAI-compatible endpoint (free), also validated live. Swap by one env var, `MODEL_PROVIDER`:
`claude` (default) | `glm`. The verdict is identical across them by construction, and any
other OpenAI-compatible brain swaps in the same way. No code edit. The `claude` path uses
`langchain-anthropic`; the `glm` path reuses `langchain-openai`.

---

## From the AVL workshop

This engine is a verbatim port of `tools/jalankan_saringan.py` from the
Bengkel Saham AI Advanced Class. It preserves the exact screening criteria,
thresholds, and refusal-first behavior. The synthetic datasets (`data/ORKES-*.json`)
are unchanged — same 6 companies, same expected outcomes.

---

## License

MIT — the doctrine is the differentiator, not the code.
