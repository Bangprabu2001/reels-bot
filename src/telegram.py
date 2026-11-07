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
        [{"text": "🎯 Buat 1 video kuis", "callback_data": "b:1"}],
        [{"text": "🎯🎯🎯 Buat 3 video kuis", "callback_data": "b:3"}],
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


def format_paket(pk):
    L = [f"🎯 Kuis siap | Lucu {pk['kualitas'].get('lucu', '-')}/10, orisinal {pk['kualitas'].get('orisinal', '-')}/10",
         f"🏷 Tema gelar: {pk['tema']}", f"⏱ Durasi: {pk['durasi']:.0f} detik", "", "❓ Soal:"]
    for i, s in enumerate(pk["soal"], 1):
        L.append(f"{i}. {s['q']}  →  {s['a']}")
    L += ["", "🏆 Gelar:"] + [f"- {g['nama']}" for g in pk["gelar"]]
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
