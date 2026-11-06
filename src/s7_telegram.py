"""TAHAP 7 - KIRIM KE TELEGRAM."""
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
        [{"text": "🎬 MODE 1 · Dua Nasib (split screen)", "callback_data": "m:1"}],
        [{"text": "🕌 MODE 2 · Paper-cut Dakwah", "callback_data": "m:2"}],
        [{"text": "📊 MODE 3 · Bedah Bisnis Blueprint", "callback_data": "m:3"}],
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
    L = [f"🎬 MODE {pk['mode']} | Skor penilaian diri: {pk['skor']:g}/10",
         f"📌 Topik: {pk['topik']}", "", "🏷 3 pilihan judul:"]
    for i, j in enumerate(pk["judul_pilihan"][:3], 1):
        L.append(f"{i}. {j}")
    L += ["", "📝 Caption:", pk["caption"], "", " ".join(pk["hashtag"])]
    if pk.get("sumber"):
        L += ["", "📚 Sumber data:"]
        for s in pk["sumber"][:6]:
            L.append(f"- {s.get('judul') or 'sumber'}: {s['url']}")
    if pk.get("catatan"):
        L += ["", "⚠️ Catatan:"] + [f"- {c}" for c in pk["catatan"]]
    return "\n".join(L)


def kirim_hasil(chat, job, pk, mp4, thumb):
    with open(mp4, "rb") as f:
        tg("sendVideo", files={"video": f}, chat_id=chat, caption=f"{pk['judul_pilihan'][0]}"[:1000],
           supports_streaming=True, width=720, height=1280)
    if thumb:
        with open(thumb, "rb") as f:
            tg("sendPhoto", files={"photo": f}, chat_id=chat, caption="Thumbnail")
    kirim_teks(chat, format_paket(pk), keyboard(job))
