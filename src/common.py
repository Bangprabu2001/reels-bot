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
_model = None


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


def pick_model():
    """Pilih model Flash terbaru yang bisa dipakai. Bisa dipaksa lewat GEMINI_MODEL."""
    global _model
    if _model:
        return _model
    forced = os.environ.get("GEMINI_MODEL", "").strip()
    if forced:
        _model = forced
        return _model
    try:
        r = requests.get(f"{GEM}/models", params={"key": _key(), "pageSize": 200}, timeout=60)
        best, best_v = None, -1.0
        for m in r.json().get("models", []):
            name = m.get("name", "").replace("models/", "")
            if "generateContent" not in m.get("supportedGenerationMethods", []):
                continue
            if "flash" not in name or any(x in name for x in ("lite", "image", "tts", "live", "audio", "thinking", "robotics", "embedding")):
                continue
            mv = re.search(r"gemini-(\d+(?:\.\d+)?)-flash", name)
            if not mv:
                continue
            v = float(mv.group(1))
            if v > best_v or (v == best_v and best and "preview" in best and "preview" not in name):
                best, best_v = name, v
        _model = best or "gemini-2.5-flash"
    except Exception:
        _model = "gemini-2.5-flash"
    log(f"[gemini] model dipakai: {_model}")
    return _model


def _call(prompt, system, json_out, grounded, temperature, retries=4):
    global _last_call
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if grounded:
        body["tools"] = [{"google_search": {}}]
    elif json_out:
        body["generationConfig"]["responseMimeType"] = "application/json"
    last_err = ""
    for i in range(retries):
        wait = MIN_GAP - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        r = requests.post(f"{GEM}/models/{pick_model()}:generateContent",
                          params={"key": _key()}, json=body, timeout=240)
        _last_call = time.time()
        if r.status_code in (429, 500, 503):
            last_err = f"{r.status_code}"
            time.sleep(12 * (i + 1))
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Gemini error {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            cand = data["candidates"][0]
            text = "".join(p.get("text", "") for p in cand["content"]["parts"])
        except Exception:
            raise RuntimeError(f"Gemini tidak memberi jawaban: {str(data)[:300]}")
        sources, seen = [], set()
        for ch in cand.get("groundingMetadata", {}).get("groundingChunks", []):
            w = ch.get("web")
            if w and w.get("uri") and w["uri"] not in seen:
                seen.add(w["uri"])
                sources.append({"judul": w.get("title", ""), "url": w["uri"]})
        return text, sources
    raise RuntimeError(f"Gemini sibuk/limit habis ({last_err}). Coba lagi nanti.")


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
