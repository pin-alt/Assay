# Assay — cover image prompt (ChatGPT Image / DALL·E 3)

16:9 submission cover. Must read as a **thumbnail** in a grid of dozens of entries:
one focal idea, the wordmark, the wedge. Matches the deck's certificate-light identity.

The single idea: **a number that looks approved is actually wrong, and a recompute catches it.**
That is the whole pitch (correctness, not honesty) in one image.

---

## Prompt (paste into ChatGPT Image, request 16:9)

```
A flat, editorial "certificate of audit" cover image, 16:9, in the style of a notarized
financial working paper or a metallurgical assay certificate. Clean off-white paper background
(#fbfcfd), generous negative space, thin hairline ruled lines like an accounting ledger.

Centered upper-left, a large refined serif wordmark "ASSAY" in near-black ink (#1f242e),
with a small monospaced label beneath it reading "CERTIFICATE OF AUDIT" in wide letter-spacing.

The focal element, center: a small bordered "report" card showing a financial line item —
the label "gearing" and the value "0.01" with a green check mark next to it, looking approved
and honest. Overlapping it at an angle, a precise deep-red rubber audit stamp reading
"AUDIT: FAIL" (#b23a2c), and a monospaced correction note: "engine computes 0.26". A thin
deep-indigo (#3a4a9a) embossed certificate seal sits in the lower corner.

One tagline along the bottom in clean serif: "Agents that prove their numbers are right."

Mood: precise, restrained, accountable, high-stakes, document-of-record. Muted and editorial,
not glossy. Palette limited to off-white, near-black ink, one deep indigo, one deep green for
the check, one deep red for the stamp. Crisp flat vector / risograph print feel, subtle paper
grain. Everything legible at small thumbnail size.
```

---

## Spec / guardrails

- **Aspect:** 16:9. Lablab cover slot.
- **Palette (limit to these):** paper `#fbfcfd` · ink `#1f242e` · indigo `#3a4a9a` · verified green `#2f7d50` · alarm red `#b23a2c`.
- **Text in image:** keep to `ASSAY`, `CERTIFICATE OF AUDIT`, the `gearing 0.01 ✓` line, the `AUDIT: FAIL` stamp, `engine computes 0.26`, and the tagline. If the model garbles any text (image models often do), regenerate, or generate it text-light and overlay the exact words in Canva/Figma after.
- **Hard NO (anti-references):** no neon, no crypto/moon-shot energy, no glowing circuits or robots/androids, no glossy 3D render, no generic blue fintech gradient, no busy dashboard, no stock "AI brain." Restrained regulated-workflow posture only.
- **Why this beats a generic cover:** it telegraphs the wedge (a wrong-but-honest number, caught by recompute) at thumbnail size, and the certificate motif signals Track 3 (regulated, accountable) without a word of explanation.

## Fallback if image text keeps breaking
Generate the certificate/stamp scene **without** the small data text, then overlay in Canva:
`ASSAY` (serif), tagline (serif), and the mono block `gearing 0.01 ✓ → AUDIT: FAIL · engine computes 0.26`.
