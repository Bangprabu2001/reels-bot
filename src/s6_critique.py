"""TAHAP 6 - SELF-CRITIQUE: nilai 1-10, di bawah 8 diulang."""
import json
import re

from .common import cek_perhitungan, gemini_json, log
from .s2_router import pelanggaran_prompt, rules_block

KALIMAT_PEMBUKA = {
    "1": ("bayangkan", "Voiceover babak 1 harus diawali 'Bayangkan... Dua orang ini...'"),
    "3": ("pov", "Voiceover babak 1 harus diawali 'POV: Kamu Adalah Pemilik ...'"),
}


def _cek_keras(cerita, prompts, mode):
    """Pemeriksaan otomatis yang tidak bergantung pada AI."""
    m = []
    babak = cerita.get("babak", [])
    if len(babak) != 4:
        m.append(f"jumlah babak {len(babak)}, harus 4")
        return m
    for b in babak:
        if not str(b.get("voiceover", "")).strip():
            m.append(f"babak {b['no']} tanpa voiceover")
    m += cek_perhitungan(cerita.get("perhitungan"))
    m += pelanggaran_prompt(mode, prompts)
    vo1 = babak[0].get("voiceover", "").lower()
    if mode["id"] in KALIMAT_PEMBUKA and KALIMAT_PEMBUKA[mode["id"]][0] not in vo1[:60]:
        m.append(KALIMAT_PEMBUKA[mode["id"]][1])
    vo4 = babak[3].get("voiceover", "").strip()
    if mode["id"] == "1" and "?" not in vo4[-80:]:
        m.append("kalimat penutup MODE 1 harus pertanyaan refleksi")
    if mode["id"] == "1":
        for i in (1, 2, 3):
            if not babak[i].get("angka_melayang"):
                m.append(f"MODE 1 babak {i + 1} wajib punya angka_melayang")
    if mode["id"] == "2":
        if not babak[1].get("dalil"):
            m.append("MODE 2 babak 2 wajib punya dalil (Arab + arti)")
        if not babak[2].get("kitab") or len(babak[2]["kitab"]) < 2:
            m.append("MODE 2 babak 3 wajib 2 kitab berdampingan")
        if any(b.get("angka_melayang") for b in babak):
            m.append("MODE 2 dilarang angka melayang")
    if mode["id"] == "3":
        if not cerita.get("pov_label"):
            m.append("MODE 3 wajib pov_label untuk bar letterbox atas")
        if not babak[1].get("tabel"):
            m.append("MODE 3 babak 2 wajib tabel modal")
        if not babak[2].get("tabel") or not babak[2].get("mitos_realita"):
            m.append("MODE 3 babak 3 wajib tabel dan mitos_realita")
        if not babak[3].get("grafik"):
            m.append("MODE 3 babak 4 wajib grafik")
    return m


def nilai(cerita, prompts, mode, riset):
    """Mengembalikan {skor, masalah[], saran}. Skor dibatasi 7 kalau ada pelanggaran keras."""
    keras = _cek_keras(cerita, prompts, mode)
    prompt = f"""Kamu SELF-CRITIC yang keras dan jujur. Nilai hasil kerja ini dari 1-10 terhadap RULE MODE.

{rules_block(mode)}

CERITA: {json.dumps(cerita, ensure_ascii=False)[:9000]}
PROMPT GAMBAR: {json.dumps(prompts, ensure_ascii=False)}
DATA RISET (pegangan fakta): {json.dumps({k: riset.get(k) for k in ('ringkasan', 'fakta', 'angka_kunci', 'dalil', 'pendapat')}, ensure_ascii=False)[:5000]}

Periksa: (a) apakah ada rule/larangan mode yang dilanggar atau tercampur gaya mode lain, (b) apakah emosi tujuan tercapai,
(c) apakah ada angka/dalil yang tidak ada di data riset (mengarang), (d) apakah panjang voiceover cocok dengan durasi 75 detik,
(e) apakah sudut pandangnya benar-benar baru dan tidak generik.
Jawab HANYA JSON: {{"skor": 1-10, "masalah": ["..."], "saran": "perintah perbaikan singkat dan jelas untuk penulis"}}"""
    try:
        h = gemini_json(prompt, temperature=0.2)
        skor = float(h.get("skor", 5))
        masalah = list(h.get("masalah", []))
        saran = h.get("saran", "")
    except Exception as e:
        log(f"[kritik] AI gagal menilai: {e}")
        skor, masalah, saran = 6.0, ["penilaian AI gagal"], ""
    if keras:
        skor = min(skor, 7.0)
        masalah = keras + masalah
        saran = "WAJIB perbaiki: " + "; ".join(keras) + ". " + saran
    log(f"[kritik] skor {skor:g}, masalah keras: {len(keras)}")
    return {"skor": skor, "masalah": masalah, "saran": saran, "keras": keras}
