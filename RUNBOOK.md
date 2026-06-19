# Assay — Live Demo Runbook (your part, step by step)

Goal: get the 3-agent desk running live on Band, catch a doctored report on camera, capture
evidence, and submit before Jun 19, 11:00 AM EDT. Code is done; this is the manual part.

Two kinds of step below:
- **[TERMINAL]** = run in a PowerShell window you keep open (the working dir is this folder).
- **[BROWSER]** = do it on app.band.ai / lablab.ai.

The agent process blocks (it holds a WebSocket open), so run it in its OWN terminal window
and leave it running while you switch to the browser.

---

## Phase 0 — Prove the environment works (5 min, before touching Band)

[TERMINAL]
```
uv sync --extra dev
uv run pytest -q
uv run python -m armada.runner --demo
```
Expect: `24 passed`, then a table `PASS: 2 | FAIL: 2 | INCOMPLETE: 2`.
If this works, the engine + auditor are healthy and the only unknowns left are Band + the LLM.

---

## Phase 1 — Register the 3 agents on Band (10 min)

[BROWSER] Go to https://app.band.ai/agents. For each of the three, click the blue
**Connect Remote Agent** button (NOT "Create Internal Agent" — internal = Band-hosted, which
won't run our engine/tools; our agents are remote Python processes that connect in). Use
these names + descriptions:

- **Skaut** — "Discovery agent. Surveys the company dataset and returns a candidate list with a completeness pre-check. Never computes a ratio."
- **Konduktor** — "Orchestrator and report writer. Runs the screening desk: recruits Skaut,
  runs the deterministic engine, writes reports, recruits Pengulas to audit each one."
- **Pengulas** — "Cross-auditor. Re-runs the deterministic engine to verify every report and
  returns AUDIT: PASS or AUDIT: FAIL."

Do NOT use generic names like "Assistant" or "AI".

For EACH agent, copy two things from its settings page:
1. **Agent UUID** (the agent_id)
2. **API Key** (shown once — copy it immediately)

You now have 6 values (3 agents × {id, key}).

Skaut 

---

## Phase 2 — Fill the two secret files (5 min)

[TERMINAL]
```
cp agent_config.yaml.example agent_config.yaml
cp .env.example .env
```

[EDITOR] Open `agent_config.yaml`, paste each agent's UUID + key:
```yaml
skaut:
  agent_id: "….."
  api_key: "….."
konduktor:
  agent_id: "….."
  api_key: "….."
pengulas:
  agent_id: "….."
  api_key: "….."
```

[EDITOR] Open `.env`, set your z.ai key, leave the rest as-is for now:
```
MODEL_PROVIDER=glm
GLM_API_KEY=<your z.ai key>
```

[TERMINAL] Confirm both files are gitignored (so secrets never get committed):
```
git check-ignore .env agent_config.yaml
```
Expect: both paths printed. If nothing prints, STOP — do not commit until they're ignored.

---

## Phase 3 — First live smoke + lock the brain (15 min)

[TERMINAL] (own window, leave it running)
```
uv run python -m armada.runner --all
```
Expect: three lines `[+] Starting skaut/konduktor/pengulas (agent_id=…)`, then it stays up.

[BROWSER] On app.band.ai confirm Skaut, Konduktor, Pengulas show as online/available.

**If the brain misbehaves** (this is the one real risk):
- `429 "insufficient balance"` (GLM backup) → it's the billing path, not a dead key. In `.env`
  set `GLM_BASE_URL=https://api.z.ai/api/coding/paas/v4/`, save, Ctrl+C the agents, re-run.
- Agents loop / never finish / malformed tool calls → switch the brain (one line in `.env`):
  `MODEL_PROVIDER=claude` (primary, most reliable; `langchain-anthropic` is already installed)
  or `MODEL_PROVIDER=glm`. Ctrl+C, re-run `--all`. Do NOT spend hours tuning prompts; swap and move on.

Rule: whatever brain runs the full cycle cleanly in Phase 4 is the brain you RECORD on. Never
change it between the run you validated and the run you record.

---

## Phase 4 — Run the Rondaan cycle (the core demo, 15 min)

[BROWSER] app.band.ai → Chats → new chat room:
- Name it `Rondaan Room`
- Add all three agents (Skaut, Konduktor, Pengulas) as participants.

Type into the room:
```
@Konduktor Run a full rondaan — screen all companies, write reports, and audit each one.
```

Watch for (this IS the win-gate — it must be visible on screen):
1. Konduktor @mentions **Skaut** → Skaut returns the candidate list.
2. Konduktor calls `run_screening` → a **tool_call** entry appears in the room/trail, then a
   **tool_result**.
3. Konduktor writes reports, @mentions **Pengulas** per report.
4. Pengulas returns **AUDIT: PASS** for each.
5. Konduktor posts the summary: 2 LULUS, 2 GAGAL, 2 TIDAK LENGKAP (refused), ending in a
   **Human sign-off** block (`AWAITING HUMAN SIGN-OFF`).

[TERMINAL] Confirm reports landed:
```
ls output/
```
Expect 4 `Report_*.md` (or `Laporan_*.md`) + 1 `Rondaan_*.md`.

If you see "Internal error while processing message" in the chat: an @mention handle didn't
resolve. Re-check the 3 agents are all in the room with the exact names above, and re-send.

---

## Phase 5 — The kill shot: catch a doctored report (10 min)

This is the most important 30 seconds of your demo. Two ways; do at least the CLI one (it
can't fail on camera, no LLM involved).

**Way A — live, through Band:**
[EDITOR] Open one finished report in `output/`, find the `armada-claims` block, change one
number (e.g. `"gearing": 0.26` → `"gearing": 0.01`), save.
[BROWSER] In the room:
```
@Pengulas audit output/Report_ORKES-A.md
```
Expect: **AUDIT: FAIL** naming the exact discrepancy.

**Way B — deterministic CLI (bulletproof, no LLM):**
[TERMINAL]
```
uv run python -m armada.audit output/Report_ORKES-A.md data ORKES-A
```
Expect (clean): `AUDIT: PASS`. After doctoring a number:
`AUDIT: FAIL  Details: gearing: report claims 0.01, engine computes 0.26`

The line to say while showing it: *"A hash proves nobody altered the report. It doesn't prove
the report is right. We prove it by recomputing it."*

---

## Phase 6 — Capture evidence (10 min)

[TERMINAL]
```
mkdir -p ../2026-05-23-investment-advisor/hackathon/evidence
cp output/Report_*.md output/Rondaan_*.md ../2026-05-23-investment-advisor/hackathon/evidence/ 2>/dev/null
```
[BROWSER] Screenshot into that `evidence/` folder:
1. The @mention handoffs (Konduktor→Skaut→Pengulas) in the room.
2. The `tool_call` / `tool_result` entries in Band's audit trail.
3. The AUDIT: FAIL (live and/or the CLI).
4. The Human sign-off block at the end of the summary.

---

## Phase 7 — Record the video (script is in hackathon/media.md)

- Record at 1080p (OBS or Loom), 2:30–3:00. Follow `hackathon/media.md` beat by beat.
- Lead with the wedge: "others audit whether the AI was honest; we re-run the math and catch
  wrong-even-when-honest."
- Show the Band trail (win-gate), then the AUDIT: FAIL (kill shot), close on human sign-off.
- Record on the LOCKED brain from Phase 3.

---

## Phase 8 — Cover + deck (heaviest non-code gap)

The diadvisor `brand/` assets are the WRONG product. Minimum viable: one Assay cover
image (16:9) + use this README / the live demo as the "deck". A full deck is optional if time
is short — the video matters more.

---

## Phase 9 — Submit (do NOT rush this)

[BROWSER] On lablab.ai, fill the form from `hackathon/band-of-agents-submission.md` (every
field is pre-measured to fit). Track 3.
- Sleep-before-send: don't submit the same hour you finish the copy. Re-read once with fresh
  eyes, then submit.

---

## One-glance failure → fix table

| Symptom | Fix |
|---|---|
| `429 insufficient balance` (GLM) | `.env` GLM_BASE_URL → `https://api.z.ai/api/coding/paas/v4/` |
| Agents loop / malformed tool calls | `.env` MODEL_PROVIDER=claude (langchain-anthropic already installed) |
| "Internal error while processing message" in chat | an @mention didn't resolve — confirm all 3 agents are in the room with exact names |
| No tool_call/tool_result in the trail | re-pull latest (emit gate fix is committed); confirm you're on the current code |
| Report not found on audit | use the filename as written in output/ (with or without the `output/` prefix both work) |
| Demo flaky on camera | use the `python -m armada.audit` CLI for the kill shot — no LLM, can't fail |
