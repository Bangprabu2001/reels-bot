"""Fungsi bantu yang dipakai semua tahap."""
import ast
import difflib
import json
import operator
import os
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

GEM = "https://generativelanguage.googleapis.com/v1beta"
MIN_GAP = 4.5  # detik antar panggilan Gemini (jaga batas gratis ~15 per menit)
_last_call = 0.0


def log(*a):
    print(*a, flush=True)


def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- Gemini
def _key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        raise RuntimeError("GEMINI_API_KEY belum diisi di GitHub Secrets.")
    return k


_daftar = None
_habis = {}              # model -> waktu (epoch) boleh dicoba lagi
_tanpa_thinking = set()  # model yang menolak pengaturan thinking
MODEL_TERPAKAI = []      # model yang benar-benar menjawab (untuk catatan di Telegram)
CADANGAN = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]


def daftar_model():
    """Urutan model: stabil dulu (versi terbaru di atas), lalu preview, lalu 'lite'. GEMINI_MODEL jadi pilihan pertama."""
    global _daftar
    if _daftar is not None:
        return _daftar
    ranking = []
    try:
        r = requests.get(f"{GEM}/models", params={"key": _key(), "pageSize": 200}, timeout=30)
        for m in r.json().get("models", []):
            name = m.get("name", "").replace("models/", "")
            if "generateContent" not in m.get("supportedGenerationMethods", []):
                continue
            if "flash" not in name or any(x in name for x in ("image", "tts", "live", "audio", "robotics", "embedding", "thinking", "native")):
                continue
            mv = re.search(r"gemini-(\d+(?:\.\d+)?)-flash", name)
            if mv:
                ranking.append((("lite" in name, "preview" in name or "-exp" in name, -float(mv.group(1))), name))
    except Exception as e:
        log(f"[gemini] gagal membaca daftar model: {e}")
    ranking.sort()
    names = []
    for _, n in ranking:
        if n not in names:
            names.append(n)
    if not names:
        names = list(CADANGAN)
    forced = os.environ.get("GEMINI_MODEL", "").strip()
    if forced:
        names = [forced] + [n for n in names if n != forced]
    _daftar = names
    log(f"[gemini] urutan model: {', '.join(names[:6])}")
    return names


def model_aktif():
    now = time.time()
    for n in daftar_model():
        if _habis.get(n, 0) <= now:
            return n
    return None


def tandai_habis(model, detik, alasan):
    _habis[model] = time.time() + detik
    nxt = model_aktif()
    log(f"[gemini] {model} {alasan}; " + (f"pindah ke {nxt}" if nxt else "semua model sedang tidak bisa dipakai"))


def _call(prompt, system, json_out, grounded, temperature, retries=12, max_tokens=8192):
    global _last_call
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    thinking_off = os.environ.get("GEMINI_THINKING", "") != "1"
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if grounded:
        body["tools"] = [{"google_search": {}}]
    elif json_out:
        body["generationConfig"]["responseMimeType"] = "application/json"
    gagal, sudah_menunggu = {}, False
    for _ in range(retries):
        model = model_aktif()
        if model is None:
            sisa = min(_habis.values()) - time.time()
            if 0 < sisa <= 120 and not sudah_menunggu:
                sudah_menunggu = True
                log(f"[gemini] semua model kena batas sementara, menunggu {sisa:.0f} detik")
                time.sleep(sisa + 1)
                continue
            raise RuntimeError("Kuota semua model Gemini sedang habis. Coba lagi nanti "
                               "(kuota harian gratis biasanya reset sore hari sekitar jam 14.00-15.00 WIB).")
        cfg = body["generationConfig"]
        if thinking_off and model not in _tanpa_thinking:
            cfg["thinkingConfig"] = {"thinkingBudget": 0}
        else:
            cfg.pop("thinkingConfig", None)
        wait = MIN_GAP - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        try:
            r = requests.post(f"{GEM}/models/{model}:generateContent",
                              params={"key": _key()}, json=body, timeout=100)
        except (requests.Timeout, requests.ConnectionError) as e:
            _last_call = time.time()
            gagal[model] = gagal.get(model, 0) + 1
            log(f"[gemini] {model}: {type(e).__name__} ({gagal[model]}x)")
            if gagal[model] >= 2:
                tandai_habis(model, 300, "tidak merespons")
            time.sleep(5)
            continue
        _last_call = time.time()
        teks = r.text.lower()
        if r.status_code == 429:
            harian = "perday" in teks or "per day" in teks or "daily" in teks
            tandai_habis(model, 21600 if harian else 70, "kuota habis (harian)" if harian else "kena batas per menit")
            continue
        if r.status_code == 404 or (r.status_code == 400 and "not found" in teks):
            tandai_habis(model, 86400, "tidak tersedia")
            continue
        if r.status_code == 400 and "thinking" in teks and "thinkingConfig" in cfg:
            _tanpa_thinking.add(model)
            log(f"[gemini] {model} menolak pengaturan thinking, diulang tanpa itu")
            continue
        if r.status_code in (500, 503):
            gagal[model] = gagal.get(model, 0) + 1
            log(f"[gemini] {model} status {r.status_code} ({gagal[model]}x)")
            if gagal[model] >= 2:
                tandai_habis(model, 300, "sedang bermasalah")
            time.sleep(6)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Gemini error {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            cand = data["candidates"][0]
            text = "".join(p.get("text", "") for p in cand["content"]["parts"])
        except Exception:
            tandai_habis(model, 120, "tidak memberi jawaban")
            continue
        if model not in MODEL_TERPAKAI:
            MODEL_TERPAKAI.append(model)
        sources, seen = [], set()
        for ch in cand.get("groundingMetadata", {}).get("groundingChunks", []):
            w = ch.get("web")
            if w and w.get("uri") and w["uri"] not in seen:
                seen.add(w["uri"])
                sources.append({"judul": w.get("title", ""), "url": w["uri"]})
        return text, sources
    raise RuntimeError("Gemini tidak berhasil menjawab setelah beberapa kali mencoba model. Coba lagi nanti.")


def gemini_text(prompt, system=None, temperature=0.8):
    return _call(prompt, system, False, False, temperature)[0]


def gemini_json(prompt, system=None, temperature=0.8):
    text, _ = _call(prompt, system, True, False, temperature)
    return extract_json(text)


def gemini_grounded(prompt, system=None, temperature=0.3):
    """Gemini + Google Search. Mengembalikan (teks, daftar_sumber)."""
    return _call(prompt, system, False, True, temperature)


def extract_json(text):
    t = text.strip()
    t = re.sub(r"^```(?:json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    starts = [i for i in (t.find("{"), t.find("[")) if i != -1]
    if not starts:
        raise ValueError("Tidak ada JSON di jawaban AI.")
    s = min(starts)
    e = max(t.rfind("}"), t.rfind("]"))
    chunk = t[s:e + 1]
    try:
        return json.loads(chunk)
    except json.JSONDecodeError:
        chunk = re.sub(r",\s*([}\]])", r"\1", chunk)
        return json.loads(chunk)


# ---------------------------------------------------------------- hitung aman
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos, ast.Mod: operator.mod}


def safe_calc(expr):
    """Hitung rumus aritmetika sederhana tanpa eval berbahaya."""
    # rumus wajib angka polos: tanpa titik ribuan, desimal pakai titik (contoh 15000*300*30)
    expr = str(expr).replace("×", "*").replace("÷", "/").replace("^", "**").replace(" ", "")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("rumus tidak aman")
    return ev(ast.parse(expr, mode="eval"))


def cek_perhitungan(daftar):
    """Cek tiap {label, rumus, hasil}. Mengembalikan daftar masalah (kosong = benar semua)."""
    masalah = []
    for item in daftar or []:
        try:
            nilai = float(safe_calc(item["rumus"]))
            hasil = float(str(item["hasil"]).replace(",", "."))
            tol = max(abs(hasil) * 0.02, 0.01)
            if abs(nilai - hasil) > tol:
                masalah.append(f"'{item.get('label')}': rumus {item['rumus']} = {nilai:g}, tapi tertulis {hasil:g}")
        except Exception as e:
            masalah.append(f"'{item.get('label')}': rumus tidak bisa dihitung ({e})")
    return masalah


# ---------------------------------------------------------------- database topik
DB_PATH = DATA / "topics_db.json"


def load_db():
    db = load_json(DB_PATH, {}) or {}
    for k in ("disetujui", "dibuang", "dibuat_ulang"):
        db.setdefault(k, [])
    return db


def save_db(db):
    save_json(DB_PATH, db)


def mirip(a, b):
    na = re.sub(r"[^a-z0-9 ]", "", a.lower())
    nb = re.sub(r"[^a-z0-9 ]", "", b.lower())
    r = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    j = len(ta & tb) / max(1, len(ta | tb))
    return max(r, j)


def sudah_ada(judul, db, ambang=0.6):
    for kolom in ("disetujui", "dibuang", "dibuat_ulang"):
        for item in db.get(kolom, []):
            if mirip(judul, item.get("judul", "")) >= ambang:
                return item.get("judul")
    return None
