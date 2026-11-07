"""Narator (edge-tts, gratis) dan perakit trek audio."""
import asyncio
import math
import os
import subprocess
import time
import wave
from pathlib import Path

import numpy as np

from .common import ROOT, log
from .penulis import ANGKA_KATA

SR = 24000
OFFLINE = os.environ.get("OFFLINE", "") == "1"


def skor_kata(i, n):
    """Skor untuk dibaca: tingkat 0 = n benar, 1 = n-1, 2 = n-2, 3 = 0 sampai n-3."""
    if i < 3:
        return ANGKA_KATA.get(n - i, str(n - i))
    return f"nol sampai {ANGKA_KATA.get(n - 3, str(n - 3))}"


def teks_narasi(p):
    n = len(p["soal"])
    t = {
        "hook": f"Jawab {ANGKA_KATA.get(n, n)} teka-teki ini! Lihat nilaimu di akhir.",
        "soal": [str(s["q"]) for s in p["soal"]],
        "jawab": [f"Jawabannya, {str(s['a']).rstrip('.!')}." for s in p["soal"]],     # penjelasan (a2) dibaca penonton di layar
        "intro": "Ini gelarmu!",
        "baris": [f"Benar {skor_kata(i, n)}. {g['nama']}." for i, g in enumerate(p["gelar"])],
        "penutup": "Tulis gelarmu di komentar!",
    }
    return t


async def _edge(teks, out, nama, rate, pitch):
    import edge_tts
    await edge_tts.Communicate(teks, nama, rate=rate, pitch=pitch).save(str(out))


def _ke_array(path):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ar", str(SR), "-ac", "1", "-f", "s16le", "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0 if r.returncode == 0 and r.stdout else None


def _satu(teks, folder, nama_file, cfg):
    """Satu klip suara. Gagal -> keheningan dengan durasi perkiraan (video tetap jadi)."""
    s = cfg["suara"]
    if s.get("aktif", True) and not OFFLINE:
        mp3 = Path(folder) / f"{nama_file}.mp3"
        for _ in range(3):
            try:
                asyncio.run(_edge(teks, mp3, s["nama"], s["kecepatan"], s["nada"]))
                a = _ke_array(mp3)
                if a is not None and len(a) > 0:
                    return a, True
            except Exception as e:
                log(f"[suara] {nama_file}: {e}")
                time.sleep(2)
    dur = max(1.5, len(teks.split()) / 2.4)
    return np.zeros(int(SR * dur), np.float32), False


def buat_narasi(p, folder, cfg):
    """Mengembalikan (klip, durasi, jumlah_berhasil, jumlah_total)."""
    t = teks_narasi(p)
    klip = {"hook": None, "soal": [], "jawab": [], "intro": None, "baris": [], "penutup": None}
    ok = tot = 0

    def ambil(teks, nama):
        nonlocal ok, tot
        a, b = _satu(teks, folder, nama, cfg)
        ok += int(b); tot += 1
        return a
    klip["hook"] = ambil(t["hook"], "hook")
    for i, x in enumerate(t["soal"]): klip["soal"].append(ambil(x, f"soal{i}"))
    for i, x in enumerate(t["jawab"]): klip["jawab"].append(ambil(x, f"jawab{i}"))
    klip["intro"] = ambil(t["intro"], "intro")
    for i, x in enumerate(t["baris"]): klip["baris"].append(ambil(x, f"baris{i}"))
    klip["penutup"] = ambil(t["penutup"], "penutup")
    dur = {"hook": len(klip["hook"]) / SR, "soal": [len(a) / SR for a in klip["soal"]], "jawab": [len(a) / SR for a in klip["jawab"]],
           "intro": len(klip["intro"]) / SR, "baris": [len(a) / SR for a in klip["baris"]], "penutup": len(klip["penutup"]) / SR}
    return klip, dur, ok, tot


# ------------------------------------------------------------------ efek bunyi + penyusunan trek
def _nada(a, t0, f, dur, vol, decay=7):
    n, i0 = int(SR * dur), int(SR * t0)
    if i0 >= len(a) or i0 < 0:
        return
    x = np.arange(n) / SR
    s = (np.sin(2 * math.pi * f * x) * np.exp(-x * decay) * vol)[: len(a) - i0]
    a[i0:i0 + len(s)] += s


def _taruh(a, klip, t0, vol=1.0):
    i0 = int(SR * t0)
    if i0 >= len(a):
        return
    s = klip[: len(a) - i0] * vol
    a[i0:i0 + len(s)] += s


def susun_audio(klip, jad, cfg, out_wav):
    a = np.zeros(int(SR * (jad["total"] + 0.3)), np.float32)
    # musik latar (opsional): diulang, volume kecil, menghilang di akhir
    m = cfg.get("musik", {})
    mp = ROOT / m.get("file", "")
    if m.get("aktif", True) and m.get("file") and mp.exists():
        arr = _ke_array(mp)
        if arr is not None and len(arr) > SR:
            arr = np.tile(arr, int(len(a) / len(arr)) + 1)[: len(a)] * float(m.get("volume", 0.12))
            f = int(SR * 1.5); arr[-f:] *= np.linspace(1, 0, f)
            a += arr
    n = int(SR * 0.5); x = np.arange(n) / SR
    a[:n] += np.sin(2 * math.pi * (300 + 900 * x) * x) * (1 - x / 0.5) * 0.25      # whoosh pembuka
    _taruh(a, klip["hook"], 0.15)
    for J in jad["soal"]:
        i = J["i"]
        _nada(a, J["s"], 520, 0.25, 0.3)
        _taruh(a, klip["soal"][i], J["s"] + 0.3)
        for k in range(int(J["cd"])):
            _nada(a, J["s"] + J["soal"] + k, 660, 0.18, 0.3)
        ta = J["s"] + J["soal"] + J["cd"]
        _nada(a, ta, 880, 0.8, 0.4); _nada(a, ta + 0.08, 1320, 0.8, 0.25)
        _taruh(a, klip["jawab"][i], ta + 0.5)
    R = jad["reward"]
    _taruh(a, klip["intro"], R + 0.3)
    notes = [880, 659, 523, 440]
    for k in range(4):
        _nada(a, R + jad["baris"][k], notes[k], 0.7, 0.35)
        _taruh(a, klip["baris"][k], R + jad["baris"][k] + 0.2)
    for k, f in enumerate([523, 659, 784, 1047]):
        _nada(a, R + jad["baris"][0] + 0.1 + k * 0.09, f, 1.2, 0.28, 3)
    _taruh(a, klip["penutup"], R + jad["penutup_t"] + 0.1)
    pk = float(np.max(np.abs(a))) or 1.0
    a = a / max(1.0, pk / 0.95)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32000).astype(np.int16).tobytes())
    return out_wav
