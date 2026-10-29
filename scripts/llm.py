"""Pemanggil Gemini lewat REST (tanpa library tambahan, ringan untuk laptop low-spec).

Ambil API key gratis di Google AI Studio, lalu: export GEMINI_API_KEY=...
Nama model bisa diganti lewat GEMINI_MODEL kalau model bawaan sudah tidak tersedia.
"""
import json
import os
import re
import urllib.error
import urllib.request

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


def tanya_json(system: str, user: str) -> dict:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY belum diisi.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Gemini error {e.code}: {e.read().decode()[:400]}")

    text = out["candidates"][0]["content"]["parts"][0]["text"].strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)
