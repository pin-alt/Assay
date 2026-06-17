# Assay — demo video script

Target 2:45 to 3:00. Record 1080p (OBS/Loom). Demo brain = **Claude** (clean trail).
Gloss every Malay term the first time it appears:
rondaan = patrol round · Skaut = scout · Konduktor = conductor · Pengulas = reviewer ·
LULUS = pass · GAGAL = fail · manusia memutuskan = the human decides.
(Verdicts on screen are English: PASS / FAIL / INCOMPLETE. The summary glosses pass/fail as LULUS/GAGAL; there is no "TIDAK LENGKAP" in the system, refused = INCOMPLETE.)

**Honesty rails (do not cross — these are what keep you safe under questions):**
- Two brains validated live: **GLM-5.2 and Claude**. Never say three.
- Lead the wedge with the **wrong-when-written** case, not the hand-tamper. A hash catches an edit; it cannot catch a number that was wrong the moment it was written.
- The auditor verifies the **machine-readable claims and the figures behind the verdict**, not every number in the prose. Don't claim "every number."
- It is a **screening desk**, not regulated advice. No TN 1/2022.

---

## 0:00 – 0:15 · Hook (the wedge, framed right)
**Screen:** the Rondaan Room, or the README correctness-audit line.
**Say:** "Most agents in this hackathon will happily invent a number. The smarter ones add an auditor that checks whether the AI was honest about its number. Assay does something different.
The number is computed by code, so our auditor re-runs the math and catches a figure that is wrong even when the AI was perfectly honest."

## 0:15 – 0:38 · Architecture in one breath
**Screen:** the three agents in the Band dashboard.
**Say:** "Three agents collaborate through Band, in a shared room we call a rondaan, a patrol
round. Skaut, the scout, surveys the data. Konduktor, the conductor, orchestrates and writes
the reports. Pengulas, the reviewer, audits. Between them sits a deterministic Python engine.
No agent computes a ratio. They call the engine as a tool."

## 0:38 – 1:35 · Live demo, coordination through Band
**Screen:** the Rondaan Room, all three agents joined, event filter set to **All**.
1. Type: `@Konduktor Run a full rondaan, screen all companies, write reports, and audit each one.`
2. Narrate as it happens:
   - "Konduktor has no discovery tool of its own, so it @mentions **Skaut**. Skaut returns the
     candidate list. That handoff is real, not decoration."
   - "Konduktor calls `run_screening`." **Point at the `tool_call` then `tool_result` in the
     trail.** "Every message, tool call, and result lands in Band's audit trail. The
     collaboration runs through Band, not around it."
   - "A report per complete company, then it @mentions **Pengulas** to audit each one."
3. Pengulas returns **AUDIT: PASS** on each. Summary: **2 PASS (LULUS), 2 FAIL (GAGAL), 2 INCOMPLETE**.
   **Say:** "Two pass, two fail, and two refused outright. Incomplete data, so no number and no
   report. The desk refuses rather than guess."

## 1:35 – 2:15 · The kill shot (this is the wedge — get the order right)
**Step A, the mechanism (clean, repeatable, cannot fail on camera).**
**Screen:** a finished report, then the terminal.
**Say:** "Here is the control. I change one figure in a report to a value that looks perfectly
honest." (Edit the `armada-claims` block: `gearing 0.26 → 0.01`.) Then run:
```
uv run python -m armada.audit output/Report_ORKES-A.md data ORKES-A
# AUDIT: FAIL  Details: gearing: report claims 0.01, engine computes 0.26
```
"No model in that verdict. It re-derived the number from source and caught it."

**Step B, the real proof (the part a hash cannot do).**
**Screen:** the GLM session export showing an AUDIT: FAIL with a real discrepancy (no tamper).
**Say:** "Now, catching an edit is not special. A tamper-evident hash catches edits too. The
hard part is a number that was wrong the moment it was written. Here is our GLM brain
mis-copying a ratio on its own, with nobody tampering. The report's hash is perfectly valid,
and the figure is still wrong. Pengulas re-ran the engine and caught it. A hash proves nobody
altered the report. It cannot prove the report was right when it was written. We recompute, so
we can."

## 2:15 – 2:35 · One control, any brain + posture
**Screen:** the `.env` `MODEL_PROVIDER` line.
**Say:** "The verdict lives in code, not the model. No model ever touches a number, so flip one
env var and the AUDIT result is byte-identical. We validated that live on two brains, GLM-5.2
and Claude. Same round, same verdict. And the desk only screens and audits. Every round ends
AWAITING HUMAN SIGN-OFF. Manusia memutuskan. The human decides."

## 2:35 – 2:55 · Close (the buyer, why it matters)
**Screen:** the Rondaan summary ending on the sign-off block.
**Say:** "Put this on a compliance or risk desk. A figure that looks honest but is wrong clears
review, and a financial restatement costs a company about nine percent of its share price on
average. A hash audit waves it through. We re-run the math and catch it. Only the engine is
domain-specific, so the same control fits underwriting, claims, ESG, or tax. AI directs, code
computes, humans decide. Synthetic data, twenty-four tests green. Not investment advice."

---

## Pre-flight (before you hit record)
- Brain locked = **Claude** (`MODEL_PROVIDER=claude`). Agents already running and connected
  (`uv run python -m armada.runner --all`) before recording.
- Band event filter = **All** (Tool call / Tool result visible in the trail).
- Terminal in the project dir, the CLI line **pre-typed, not run**.
- One clean report set (all PASS) ready. Know the edit: claims `gearing 0.26 → 0.01`. Revert after.
- The GLM AUDIT: FAIL artifact open and ready (the no-tamper proof). If you can't show it on
  screen, narrate it and keep the evidence file in the submission.
- Close notifications and extra tabs. **No `.env` on screen.** Zoom fonts up for a paused frame.
- **Dry-run once without recording**, then record.

## Win-critical
- **Band visibly the fabric.** The 0:38 beat (the @mention handoffs + `tool_call` / `tool_result`
  in the trail) is what answers the "thin wrapper" rejection. Confirm it renders on screen.
- **Lead correctness, in the right order.** Mechanism first (CLI), then the wrong-when-written
  proof (GLM self-error). Do not let the demo look like "we catch edits."
- **No overclaim.** Two brains, not three. Screening desk, not advice. Claims block and verdict
  figures, not every number.

## Evidence to keep in the submission folder
- `band-session-export-claude-clean.json` — clean 3-agent run (Skaut handoff, 4 PASS, sign-off).
- The GLM session export showing the unprompted AUDIT: FAIL (the wrong-when-written proof).
- `Report_ORKES-*.md` + `Rondaan_*.md` — deterministic output.
- The terminal `AUDIT: FAIL` screenshot (the CLI control).
