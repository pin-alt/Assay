"""Deterministic screening engine — the ONLY source of financial ratios and status.

Ported verbatim from the AVL workshop's tools/jalankan_saringan.py. Pure Python
stdlib, no LLM, no network. Same inputs always produce the same outputs.

Doctrine: numbers come from here, never from an agent's reasoning. Agents call
these functions and report what the code computed; they never compute a ratio.
"""

from __future__ import annotations

import json
from pathlib import Path

MEDAN_SYARIKAT = ["nama", "ticker", "nota", "papan", "sektor", "harga_semasa",
                  "bil_saham_juta", "kewangan"]
MEDAN_TAHUN = ["hasil_juta", "untung_bersih_juta", "aliran_tunai_operasi_juta",
               "jumlah_hutang_juta", "ekuiti_juta"]


def _check_fields(data: dict) -> list[str]:
    """Return list of missing fields. Empty list = data complete."""
    hilang = [m for m in MEDAN_SYARIKAT if m not in data]
    kewangan = data.get("kewangan", {})
    if "kewangan" not in hilang and len(kewangan) < 2:
        hilang.append("kewangan (perlu sekurang-kurangnya 2 tahun kewangan)")
    for tahun, baris in sorted(kewangan.items()):
        for m in MEDAN_TAHUN:
            if m not in baris:
                hilang.append(f"{tahun}.{m}")
    return hilang


def _compute_ratios(baris: dict) -> dict:
    """Compute ratios for one financial year. Input must be pre-validated present."""
    untung = baris["untung_bersih_juta"]
    ekuiti = baris["ekuiti_juta"]
    return {
        "gearing": round(baris["jumlah_hutang_juta"] / ekuiti, 2),
        "margin_bersih_pct": round(100.0 * untung / baris["hasil_juta"], 1),
        "roe_pct": round(100.0 * untung / ekuiti, 1),
        "untung_bersih_juta": untung,
        "aliran_tunai_operasi_juta": baris["aliran_tunai_operasi_juta"],
    }


def screen_one(data: dict) -> dict:
    """Screen one company: LULUS / GAGAL / TIDAK LENGKAP, with evidence."""
    hilang = _check_fields(data)
    if hilang:
        # Refusal-first: incomplete data gets NO ratios — only the missing-field list.
        return {
            "nama": data.get("nama", "(tiada nama)"),
            "status": "TIDAK LENGKAP",
            "medan_hilang": hilang,
            "sebab": ["data tidak lengkap, saringan dihentikan"],
            "nisbah": {},
            "kriteria": {},
        }

    tahun_semua = sorted(data["kewangan"])
    terkini = tahun_semua[-1]
    nisbah = {t: _compute_ratios(data["kewangan"][t]) for t in tahun_semua}
    n = nisbah[terkini]

    untung_semua_positif = all(nisbah[t]["untung_bersih_juta"] > 0 for t in tahun_semua)
    kriteria = {
        "K1_gearing": {"nilai": n["gearing"], "had": "< 1.0", "lulus": n["gearing"] < 1.0},
        "K2_margin_bersih_pct": {"nilai": n["margin_bersih_pct"], "had": "> 5.0",
                                  "lulus": n["margin_bersih_pct"] > 5.0},
        "K3_roe_pct": {"nilai": n["roe_pct"], "had": "> 8.0", "lulus": n["roe_pct"] > 8.0},
        "K4_untung_positif_semua_tahun": {
            "nilai": {t: nisbah[t]["untung_bersih_juta"] for t in tahun_semua},
            "had": "> 0 setiap tahun", "lulus": untung_semua_positif},
        "K5_ocf_terkini_positif": {
            "nilai": n["aliran_tunai_operasi_juta"], "had": "> 0",
            "lulus": n["aliran_tunai_operasi_juta"] > 0},
    }

    gagal = [k for k, v in kriteria.items() if not v["lulus"]]
    if gagal:
        sebab = [f"{k}: nilai {kriteria[k]['nilai']} (had {kriteria[k]['had']})" for k in gagal]
        status = "GAGAL"
    else:
        sebab = ["semua 5 kriteria lulus"]
        status = "LULUS"

    return {
        "nama": data["nama"], "status": status, "medan_hilang": [], "sebab": sebab,
        "tahun_terkini": terkini, "nisbah": nisbah, "kriteria": kriteria,
    }


def screen_all(data_dir: Path) -> dict[str, dict]:
    """Screen every *.json in data_dir. Returns {ticker: result}."""
    results: dict[str, dict] = {}
    for path in sorted(data_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        ticker = data.get("ticker", path.stem)
        results[ticker] = screen_one(data)
    return results


def list_companies(data_dir: Path) -> list[dict]:
    """Lightweight company index for discovery (no ratios computed)."""
    companies = []
    for path in sorted(data_dir.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        companies.append({
            "ticker": d.get("ticker", path.stem),
            "nama": d.get("nama", ""),
            "papan": d.get("papan", ""),
            "sektor": d.get("sektor", ""),
            "nota": d.get("nota", ""),
            "fail": path.name,
        })
    return companies
