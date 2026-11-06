"""TAHAP 2 - ROUTER: mengunci 1 mode beserta rule editingnya. Dilarang campur."""
import json
import re

from .common import CONFIG, load_json

_MODES = None


def semua_mode():
    global _MODES
    if _MODES is None:
        _MODES = load_json(CONFIG / "modes.json")
    return _MODES


def parse_perintah(teks):
    """'MODE 2, Gas 3 video' -> (2, 3). Mengembalikan None kalau bukan perintah mode."""
    m = re.search(r"mode\s*([123])", teks, re.I)
    if not m:
        return None
    n = re.search(r"gas\s*(\d+)", teks, re.I)
    jumlah = min(int(n.group(1)), 3) if n else 1
    return m.group(1), max(1, jumlah)


def kunci_mode(mode_id):
    modes = semua_mode()
    mode_id = str(mode_id)
    if mode_id not in modes:
        raise ValueError(f"MODE {mode_id} tidak ada. Pilih 1, 2, atau 3.")
    return json.loads(json.dumps(modes[mode_id]))  # salinan baru; tidak bisa tercampur


def rules_block(mode, dengan_visual=True):
    """Teks aturan lengkap satu mode, untuk disuntikkan ke prompt AI."""
    L = [f"MODE {mode['id']}: {mode['nama']} (referensi: {mode['referensi']})",
         f"TUJUAN EMOSI: {mode['tujuan_emosi']}",
         "TOPIK COCOK: " + ", ".join(mode["topik_cocok"]),
         "STRUKTUR WAJIB 4 BABAK (urutan tidak boleh dibalik):"]
    for b in mode["babak"]:
        L.append(f"  Babak {b['no']} {b['nama']} (detik {b['detik'][0]}-{b['detik'][1]}): {b['isi']}")
    if dengan_visual:
        L.append("RULE EDITING VISUAL (WAJIB SEMUA):")
        for i, r in enumerate(mode["rule_visual"], 1):
            L.append(f"  {i}. {r}")
    v = mode["voiceover"]
    L.append(f"VOICEOVER: {v['gaya']}")
    for w in v["wajib"]:
        L.append(f"  - {w}")
    L.append("DILARANG KERAS DI MODE INI: " + "; ".join(mode["dilarang"]))
    return "\n".join(L)


def pelanggaran_prompt(mode, prompts):
    """Cek prompt gambar terhadap daftar kata wajib/dilarang mode."""
    masalah = []
    for i, p in enumerate(prompts, 1):
        low = p.lower()
        mentah = p.split(". Style: ")[0].lower()  # bagian tulisan AI, tanpa gaya otomatis
        for k in mode.get("kata_dilarang_prompt", []):
            if k.lower() in mentah:
                masalah.append(f"prompt gambar {i} memuat '{k}' yang dilarang di MODE {mode['id']}")
        for k in mode.get("kata_wajib_prompt", []):
            if k.lower() not in low:
                masalah.append(f"prompt gambar {i} tidak memuat '{k}'")
    return masalah
