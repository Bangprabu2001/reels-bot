"""Suara narator dari Gemini TTS (Google AI Studio), tanpa library tambahan.

Pakai kunci GEMINI_API_KEY yang sama. Nama suara diisi lewat env SUARA (mis. Achird, Kore, Aoede, Puck,
atau nama lain yang tampil di menu suara AI Studio). Gemini TTS tidak memberi timestamp per kata,
jadi waktu tiap kata dihitung perkiraan dari panjang audio (taksir_kata).
"""
import array
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

from llm import _jeda_dari

MODELS = [
    os.environ.get("GEMINI_TTS_MODEL") or "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
]
GAYA = (
    "Read the following in Indonesian with a warm, friendly, natural tone, like a friendly teacher "
    "sharing interesting facts with a friend. Medium pace, clear pronunciation, lively but not exaggerated:\n\n"
)


def _minta(model: str, teks: str, voice: str):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY belum diisi.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": GAYA + teks}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    for p in out["candidates"][0]["content"]["parts"]:
        d = p.get("inlineData") or p.get("inline_data")
        if d:
            return base64.b64decode(d["data"]), d.get("mimeType") or d.get("mime_type") or ""
    raise KeyError("respons tidak berisi audio")


def _simpan(data: bytes, mime: str, path: Path) -> float:
    """Simpan sebagai WAV, buang hening di awal/akhir, kembalikan durasi (detik)."""
    if "wav" in mime.lower():
        path.write_bytes(data)
        with wave.open(str(path)) as w:
            return w.getnframes() / w.getframerate()
    m = re.search(r"rate=(\d+)", mime)
    laju = int(m.group(1)) if m else 24000
    a = array.array("h")
    a.frombytes(data[: len(data) // 2 * 2])
    if sys.byteorder == "big":
        a.byteswap()
    if len(a) == 0:
        raise KeyError("audio kosong")
    ambang = max(300, int(max(abs(v) for v in a) * 0.02))
    awal = next((i for i, v in enumerate(a) if abs(v) > ambang), 0)
    akhir = next((i for i in range(len(a) - 1, -1, -1) if abs(a[i]) > ambang), len(a) - 1)
    sisa = int(0.08 * laju)
    a = a[max(0, awal - sisa): min(len(a), akhir + sisa)]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(laju)
        w.writeframes(a.tobytes())
    return len(a) / laju


def sintesis(teks: str, voice: str, path: Path) -> float:
    """Buat audio narasi. Sabar saat jatah/sibuk; error RuntimeError bila tetap gagal."""
    terakhir = "tidak diketahui"
    for model in dict.fromkeys(MODELS):
        for percobaan in range(1, 4):
            try:
                data, mime = _minta(model, teks, voice)
                return _simpan(data, mime, path)
            except urllib.error.HTTPError as e:
                isi = e.read().decode()
                terakhir = f"{model} HTTP {e.code}: {isi[:200]}"
                print(f"    suara gagal: {terakhir}", flush=True)
                if e.code == 404:
                    break  # model tidak tersedia
                if e.code == 400:
                    raise RuntimeError(f"permintaan ditolak, cek nama suara '{voice}': {isi[:200]}")
                if e.code == 429:
                    jeda = _jeda_dari(isi)
                    if jeda is not None and jeda <= 70:
                        time.sleep(jeda + 1)
                        continue
                    break  # jatah model ini habis lama, coba model lain
                time.sleep(8 * percobaan)
            except (TimeoutError, urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as e:
                terakhir = f"{model}: {e!r}"
                print(f"    suara gagal: {terakhir}", flush=True)
                time.sleep(5 * percobaan)
    raise RuntimeError(f"Gemini TTS gagal. Terakhir: {terakhir}")


def taksir_kata(teks: str, durasi: float) -> list:
    """Perkiraan waktu tiap kata (sebanding panjang kata, ditambah jeda di tanda baca)."""
    kata = teks.split()
    if not kata or durasi <= 0:
        return []
    bobot = []
    for w in kata:
        b = len(re.sub(r"\W", "", w)) + 2
        if w[-1] in ",;:":
            b += 3
        elif w[-1] in ".!?":
            b += 6
        bobot.append(b)
    total = sum(bobot)
    t = 0.0
    hasil = []
    for w, b in zip(kata, bobot):
        d = durasi * b / total
        hasil.append({"teks": w, "mulai": round(t, 2), "selesai": round(t + d, 2)})
        t += d
    return hasil
