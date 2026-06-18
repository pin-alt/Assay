"""Assay — Audit Bench.

The deterministic correctness core of Assay, made self-serve. It reconstructs a
canonical screening report from the SAME engine the agents call, then runs the SAME
`audit_report()` against a fresh recompute from source. Tamper a figure and watch the
verdict flip to FAIL with no model in the loop.

This is one layer of Assay. The full three-agent Band coordination (Skaut, Konduktor,
Pengulas) is in the demo video and RUNBOOK.md — it can't live in a single web app.

Runs the real `armada.audit` / `armada.engine` (pure stdlib, no LLM, no keys).
"""

from __future__ import annotations

import glob
import json
import os

import streamlit as st

from armada.audit import CHECKED_RATIOS, audit_report, format_verdict
from armada.engine import screen_one

DATA_DIR = "data"
REPO_URL = "https://github.com/pin-alt/Assay"

st.set_page_config(
    page_title="Assay — Audit Bench",
    page_icon=":material/verified:",
    layout="centered",
)


# ── data ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_companies() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "ORKES-*.json"))):
        ticker = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            out[ticker] = json.load(fh)
    return out


def build_report(result: dict, ticker: str, overrides: dict | None = None) -> str:
    """Reconstruct the canonical report Konduktor would write, optionally tampered.

    `overrides` mutates the asserted ratios in the ARMADA-CLAIMS block — exactly the
    'wrong figure' an honest-but-mistaken report would carry.
    """
    status = result["status"]
    lines = [f"# Assay screening report — {result['name']} ({ticker})", "", f"Status: {status}", ""]

    ratios: dict = {}
    if status in {"PASS", "FAIL"}:
        latest = result["latest_year"]
        r = result["ratios"][latest]
        ratios = {k: r[k] for k in CHECKED_RATIOS}
        lines.append(f"Latest financial year audited: {latest}")
        lines.append("")
        lines.append("Key ratios (as asserted by the report):")
        shown = dict(ratios)
        if overrides:
            shown.update(overrides)
        for k in CHECKED_RATIOS:
            lines.append(f"- {k}: {shown[k]}")
        if result["reasons"]:
            lines.append("")
            lines.append("Criteria notes: " + "; ".join(result["reasons"]))
    else:
        lines.append("Refusal-first: source data is incomplete, so no ratios were computed.")
        if result.get("missing_fields"):
            lines.append("Missing: " + ", ".join(result["missing_fields"]))

    if overrides:
        ratios.update(overrides)

    claims = {"ticker": ticker, "status": status, "ratios": ratios}
    claims_block = "```armada-claims\n" + json.dumps(claims, ensure_ascii=False) + "\n```"

    lines += [
        "",
        claims_block,
        "",
        "DISCLAIMER: SYNTHETIC DATA, created for class training only. Not a real company "
        "on Bursa Malaysia. Not investment advice.",
    ]
    return "\n".join(lines)


def verdict_panel(result_text: str, ticker: str) -> dict:
    audit = audit_report(result_text, DATA_DIR, ticker)
    if audit["verdict"] == "AUDIT: PASS":
        st.success("AUDIT: PASS", icon=":material/verified:")
    else:
        st.error("AUDIT: FAIL", icon=":material/gpp_bad:")
    st.caption(f"Checks run: {audit['checks']}  ·  Discrepancies: {len(audit['discrepancies'])}  ·  no model in the verdict")
    if audit["discrepancies"]:
        for d in audit["discrepancies"]:
            st.markdown(f":red[•] {d}")
    return audit


# ── header ──────────────────────────────────────────────────────────────────
st.title("Assay — Audit Bench")
st.markdown(
    "The deterministic correctness core. Every figure is recomputed from source and the "
    "verdict is pure code, so it catches a number that is **wrong even when the report looks "
    "honest** — no stored hash, no model in the loop."
)
st.caption(
    "One layer of Assay. The three-agent Band coordination (Skaut · Konduktor · Pengulas) "
    "is in the demo video and RUNBOOK.md."
)
st.markdown(
    f":material/code: [Repository]({REPO_URL})  ·  "
    f":material/menu_book: [RUNBOOK]({REPO_URL}/blob/master/RUNBOOK.md)"
)

companies = load_companies()
labels = {t: f"{t} · {d['name']}" for t, d in companies.items()}
ticker = st.selectbox("Pick a synthetic company", list(companies), format_func=lambda t: labels[t])

result = screen_one(companies[ticker])
has_ratios = result["status"] in {"PASS", "FAIL"}

# ── tamper control ──────────────────────────────────────────────────────────
st.subheader("Tamper a figure")
overrides: dict | None = None

if has_ratios:
    latest = result["latest_year"]
    truth = result["ratios"][latest]
    tcol, vcol = st.columns([2, 1], vertical_alignment="bottom")
    with tcol:
        ratio = st.segmented_control(
            "Ratio to doctor", CHECKED_RATIOS, default="gearing", selection_mode="single"
        ) or "gearing"
    with vcol:
        claimed = st.number_input(
            f"Report claims {ratio} =",
            value=float(truth[ratio]),
            step=0.01,
            format="%.2f",
        )
    if abs(claimed - float(truth[ratio])) > 0.05:
        overrides = {ratio: claimed}
        st.caption(f"Engine recomputes {ratio} = **{truth[ratio]}** from source. Report now asserts {claimed}.")
    else:
        st.caption(f"Matches the engine ({truth[ratio]}). Move it past tolerance to forge a wrong-but-honest figure.")
else:
    inject = st.toggle("Inject a ratio into an INCOMPLETE report (violate refusal-first)")
    if inject:
        overrides = {"roe_pct": 12.0}
        st.caption("Refusal-first says INCOMPLETE data carries NO ratios. Asserting one is itself a discrepancy.")

# ── report + verdict ────────────────────────────────────────────────────────
report_text = build_report(result, ticker, overrides)
left, right = st.columns([3, 2], gap="medium")
with left:
    st.markdown("**Reconstructed report**")
    st.code(report_text, language="markdown")
with right:
    st.markdown("**Auditor verdict**")
    verdict_panel(report_text, ticker)

# ── engine table ────────────────────────────────────────────────────────────
st.subheader("Engine results — all six companies")
rows = []
for t, d in companies.items():
    r = screen_one(d)
    rows.append({
        "Ticker": t,
        "Company": r["name"],
        "Status": r["status"],
        "Reason": "; ".join(r["reasons"]) if r["reasons"]
        else ("missing: " + ", ".join(r.get("missing_fields", [])) if r["status"] == "INCOMPLETE" else "all criteria pass"),
    })
st.dataframe(rows, width="stretch", hide_index=True)
st.caption("Deterministic · pure stdlib · synthetic data · not investment advice.")
