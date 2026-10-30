"""Pemanggil Gemini lewat REST (tanpa library tambahan, ringan untuk laptop low-spec).

Ambil API key gratis di Google AI Studio, lalu: export GEMINI_API_KEY=...
Otomatis mencoba ulang kalau lambat/sibuk, dan pindah ke model cadangan kalau perlu.
Model utama bisa diganti lewat GEMINI_MODEL. Bisa menerima gambar (base64 JPEG).
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
    "gemini-flash-latest",  # nama alias: otomatis mengarah ke model flash terbaru
    "gemini-flash-lite-latest",  # versi ringan, biasanya lebih lega saat server ramai
]
TIMEOUT = 150  # detik menunggu jawaban
TRIES = 2  # percobaan per model
RONDE = 3  # berapa kali seluruh daftar model diulang kalau server sibuk
JEDA_RONDE = (60, 120)  # detik menunggu sebelum ronde berikutnya


def _panggil(model: str, system: str, user: str, thinking: bool, gambar=None) -> dict:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY belum diisi.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    config = {"responseMimeType": "application/json"}
    if thinking:
        # "berpikir" ringan supaya cepat dan hemat jatah gratis
        config["thinkingConfig"] = {"thinkingLevel": "low"}

    parts = [{"text": user}]
    for i, g in enumerate(gambar or [], 1):
        label, b64 = g if isinstance(g, tuple) else (f"Gambar {i}:", g)
        parts.append({"text": label})
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})

    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": config,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        out = json.load(r)

    hasil = out["candidates"][0]["content"]["parts"]
    text = "".join(p.get("text", "") for p in hasil if not p.get("thought")).strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)


_mati: dict = {}  # model -> waktu sampai kapan dilewati (jatah habis)


def _jeda_dari(isi: str):
    """Ambil anjuran waktu tunggu (detik) dari pesan error 429 Gemini, kalau ada."""
    m = re.search(r'retryDelay"?\s*:\s*"?(\d+(?:\.\d+)?)s', isi) or re.search(
        r"retry in (\d+(?:\.\d+)?)s", isi, re.I
    )
    return float(m.group(1)) if m else None


def tanya_json(system: str, user: str, gambar=None, ronde: int = RONDE) -> dict:
    """Tanya Gemini dan kembalikan JSON.
    - Server sibuk (503): coba model lain, lalu menunggu dan mengulang.
    - Jatah habis (429): kalau cuma jatah per menit, menunggu sesuai anjuran; kalau habis lama,
      model itu dilewati untuk sementara (hemat percobaan).
    Pakai ronde=1 untuk gagal cepat."""
    terakhir = "tidak diketahui"
    for putaran in range(1, ronde + 1):
        sibuk = False
        for model in dict.fromkeys(MODELS):
            if _mati.get(model, 0) > time.time():
                print(f"  (lewati {model}: jatah sedang habis)", flush=True)
                sibuk = True
                continue
            thinking = True
            for percobaan in range(1, TRIES + 1):
                print(f"  (AI: {model}, percobaan {percobaan})", flush=True)
                try:
                    return _panggil(model, system, user, thinking, gambar)
                except urllib.error.HTTPError as e:
                    isi = e.read().decode()
                    terakhir = f"{model} HTTP {e.code}: {isi[:300]}"
                    print(f"  gagal: {terakhir}", flush=True)
                    if e.code == 400 and thinking:
                        thinking = False  # pengaturan berpikir ditolak, coba tanpa itu
                        continue
                    if e.code == 404:
                        break  # model tidak tersedia, pindah ke model berikutnya
                    if e.code == 429:
                        sibuk = True
                        jeda = _jeda_dari(isi)
                        if jeda is not None and jeda <= 70 and percobaan < TRIES:
                            print(f"  jatah per menit habis, menunggu {jeda:.0f} detik...", flush=True)
                            time.sleep(jeda + 1)
                            continue
                        _mati[model] = time.time() + min(jeda if jeda else 150, 1800)
                        break  # model ini dilewati dulu, coba model berikutnya
                    if e.code in (500, 502, 503, 504):
                        sibuk = True
                        if percobaan < TRIES:
                            time.sleep(8 * percobaan)
                        continue
                    raise SystemExit(f"Gemini error: {terakhir}")
                except (TimeoutError, socket.timeout, urllib.error.URLError) as e:
                    sibuk = True
                    terakhir = f"{model} timeout/jaringan: {e}"
                    print(f"  gagal: {terakhir}", flush=True)
                    time.sleep(5 * percobaan)
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    terakhir = f"{model} jawaban tidak valid: {e!r}"
                    print(f"  gagal: {terakhir}", flush=True)
        if not sibuk or putaran == ronde:
            break
        jeda = JEDA_RONDE[min(putaran - 1, len(JEDA_RONDE) - 1)]
        print(f"  Gemini sedang sibuk/jatah habis. Menunggu {jeda} detik lalu mencoba lagi "
              f"(ronde {putaran + 1} dari {ronde})...", flush=True)
        time.sleep(jeda)
    raise SystemExit(f"Semua percobaan gagal. Terakhir: {terakhir}")
