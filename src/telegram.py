"""Kirim hasil ke Telegram dengan tombol."""
import json
import os

import requests

from .common import log


def _token():
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diisi di GitHub Secrets.")
    return t


def tg(method, files=None, **params):
    url = f"https://api.telegram.org/bot{_token()}/{method}"
    if files:
        data = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in params.items()}
        r = requests.post(url, data=data, files=files, timeout=300)
    else:
        r = requests.post(url, json=params, timeout=120)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram {method}: {j.get('description')}")
    return j["result"]


def keyboard(job):
    return {"inline_keyboard": [
        [{"text": "✅ SETUJU", "callback_data": f"ok:{job}"}, {"text": "🔄 BUAT ULANG", "callback_data": f"re:{job}"}],
        [{"text": "🗑 BUANG", "callback_data": f"no:{job}"}, {"text": "✏️ REVISI CAPTION", "callback_data": f"cap:{job}"}],
    ]}


def menu_markup():
    return {"inline_keyboard": [
        [{"text": "🤣 Tebak-tebakan", "callback_data": "b:tebak"}, {"text": "🧩 Teka-teki", "callback_data": "b:teka"}],
        [{"text": "🧠 Tes Psikologi", "callback_data": "b:psiko"}, {"text": "📐 Tes Logika", "callback_data": "b:logika"}],
        [{"text": "🎲 Acak 4 video (semua jenis)", "callback_data": "b:acak"}],
        [{"text": "📋 Status", "callback_data": "status"}, {"text": "🛑 Hentikan", "callback_data": "stop"}],
    ]}


def kirim_teks(chat, teks, markup=None):
    p = {"chat_id": chat, "text": teks[:4000], "disable_web_page_preview": True}
    if markup:
        p["reply_markup"] = markup
    try:
        return tg("sendMessage", **p)
    except Exception as e:
        log(f"[telegram] gagal kirim teks: {e}")


NAMA_JENIS = {"tebak": "Tebak-tebakan", "teka": "Teka-teki", "logika": "Tes Logika", "psiko": "Tes Psikologi"}


def format_paket(pk):
    jenis = pk.get("jenis", "teka")
    L = [f"🎯 {NAMA_JENIS.get(jenis, jenis)} siap | seru {pk['kualitas'].get('seru', '-')}/10",
         f"⏱ Durasi: {pk['durasi']:.0f} detik", "", "❓ Soal:"]
    for i, s in enumerate(pk["soal"], 1):
        if jenis == "psiko":
            L.append(f"{i}. {s['q']}  (A/B/C)")
        else:
            L.append(f"{i}. {s['q']}  →  {s['a']}")
    L += ["", "🏆 Hasil/level:"] + [f"- {b['label']}: {b['nama']}" for b in pk["baris"]]
    L += ["", "🏷 3 pilihan judul:"] + [f"{i}. {j}" for i, j in enumerate(pk["judul_pilihan"][:3], 1)]
    L += ["", "📝 Caption:", pk["caption"], "", " ".join(pk["hashtag"])]
    if pk.get("catatan"):
        L += ["", "⚠️ Catatan:"] + [f"- {c}" for c in pk["catatan"]]
    return "\n".join(L)


def kirim_hasil(chat, job, pk, mp4, thumb):
    with open(mp4, "rb") as f:
        tg("sendVideo", files={"video": f}, chat_id=chat, caption=str(pk["judul_pilihan"][0])[:1000],
           supports_streaming=True, width=1080, height=1920)
    if thumb:
        try:
            with open(thumb, "rb") as f:
                tg("sendPhoto", files={"photo": f}, chat_id=chat, caption="Thumbnail")
        except Exception as e:
            log(f"[telegram] thumbnail gagal: {e}")
    kirim_teks(chat, format_paket(pk), keyboard(job))
