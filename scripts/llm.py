"""Pemanggil Gemini lewat REST (tanpa library tambahan, ringan untuk laptop low-spec).

Ambil API key gratis di Google AI Studio, lalu: export GEMINI_API_KEY=...
Otomatis mencoba ulang kalau lambat/sibuk, dan pindah ke model cadangan kalau perlu.
Model utama bisa diganti lewat GEMINI_MODEL.
"""
import json
import os
import re
import socket
import time
import urllib.error
import urllib.request

MODELS = [
    os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
]
TIMEOUT = 150  # detik menunggu jawaban
TRIES = 2  # percobaan per model


def _panggil(model: str, system: str, user: str, thinking: bool) -> dict:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY belum diisi.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    config = {"responseMimeType": "application/json"}
    if thinking:
        # "berpikir" ringan supaya cepat dan hemat jatah gratis
        config["thinkingConfig"] = {"thinkingLevel": "low"}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": config,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        out = json.load(r)

    parts = out["candidates"][0]["content"]["parts"]
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)


def tanya_json(system: str, user: str) -> dict:
    terakhir = "tidak diketahui"
    for model in dict.fromkeys(MODELS):
        thinking = True
        for percobaan in range(1, TRIES + 1):
            print(f"  (AI: {model}, percobaan {percobaan})", flush=True)
            try:
                return _panggil(model, system, user, thinking)
            except urllib.error.HTTPError as e:
                terakhir = f"{model} HTTP {e.code}: {e.read().decode()[:300]}"
                print(f"  gagal: {terakhir}", flush=True)
                if e.code == 400 and thinking:
                    thinking = False  # pengaturan berpikir ditolak, coba tanpa itu
                    continue
                if e.code == 404:
                    break  # model tidak tersedia, pindah ke model berikutnya
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(10 * percobaan)
                    continue
                raise SystemExit(f"Gemini error: {terakhir}")
            except (TimeoutError, socket.timeout, urllib.error.URLError) as e:
                terakhir = f"{model} timeout/jaringan: {e}"
                print(f"  gagal: {terakhir}", flush=True)
                time.sleep(5 * percobaan)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                terakhir = f"{model} jawaban tidak valid: {e!r}"
                print(f"  gagal: {terakhir}", flush=True)
    raise SystemExit(f"Semua percobaan gagal. Terakhir: {terakhir}")
