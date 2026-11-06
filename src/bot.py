"""Pendengar Telegram (tanpa server). Dijalankan GitHub Actions tiap beberapa menit.
  python -m src.bot --cek     -> ada pesan baru dari kamu? (mengisi output ada_kerja)
  python -m src.bot --jalan   -> proses semua pesan/tombol yang masuk
  python -m src.bot --jalan --mode 2 --jumlah 1   -> langsung bikin video (jalan manual)"""
import argparse
import os
import traceback

from .common import DATA, gemini_json, load_json, log, save_json
from .s2_router import parse_perintah
from .s7_telegram import keyboard, kirim_teks, tg

STATE = DATA / "state.json"
BANTUAN = ("Halo! Ketik salah satu:\n"
           "MODE 1, Gas 1 video  (dua nasib, split screen)\n"
           "MODE 2, Gas 1 video  (paper-cut dakwah)\n"
           "MODE 3, Gas 1 video  (bedah bisnis blueprint)\n\n"
           "Setelah video datang, tekan SETUJU / BUAT ULANG / BUANG / REVISI CAPTION.\n"
           "Catatan: pesan dibaca tiap ±10 menit, jadi balasan tidak instan.")


def pemilik():
    return os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def ambil_update(state):
    return tg("getUpdates", offset=state["offset"], timeout=0, allowed_updates=["message", "callback_query"])


def cek():
    state = load_json(STATE, {"offset": 0, "menunggu_caption": {}})
    ada = False
    try:
        for u in ambil_update(state):
            m = u.get("message") or {}
            c = (u.get("callback_query") or {}).get("message", {})
            chat = str((m.get("chat") or c.get("chat") or {}).get("id", ""))
            if (pemilik() and chat == pemilik()) or (not pemilik() and m.get("text", "").startswith("/start")):
                ada = True
            else:
                state["offset"] = u["update_id"] + 1  # abaikan orang asing
                save_json(STATE, state)
    except Exception as e:
        log(f"[bot] cek gagal: {e}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"ada_kerja={'true' if ada else 'false'}\n")
    print("ada_kerja:", ada)


def revisi_caption(chat, job, instruksi):
    p = DATA / "pending" / f"{job}.json"
    pk = load_json(p)
    if not pk:
        kirim_teks(chat, "Data video itu sudah tidak ada (mungkin sudah di-SETUJU/BUANG).")
        return
    h = gemini_json(f"""Revisi caption video ini sesuai permintaan.
Topik: {pk['topik']}
Caption lama: {pk['caption']}
Hashtag lama: {' '.join(pk['hashtag'])}
Permintaan revisi: {instruksi}
Jangan menambah fakta baru. Jawab HANYA JSON: {{"caption": "...", "hashtag": ["#..."]}}""", temperature=0.7)
    pk["caption"], pk["hashtag"] = h["caption"], h["hashtag"]
    save_json(p, pk)
    kirim_teks(chat, "✏️ Caption baru:\n\n" + pk["caption"] + "\n\n" + " ".join(pk["hashtag"]), keyboard(job))


def tangani_pesan(m, state):
    from .factory import buat_video
    chat = str(m["chat"]["id"])
    teks = (m.get("text") or "").strip()
    if not pemilik():
        if teks.startswith("/start"):
            kirim_teks(chat, f"Chat ID kamu: {chat}\nSimpan angka ini di GitHub sebagai secret bernama TELEGRAM_CHAT_ID, lalu kirim /start lagi.")
        return
    if chat != pemilik():
        return  # bot pribadi: abaikan orang lain
    if teks.startswith(("/start", "/bantuan", "/help")):
        kirim_teks(chat, BANTUAN)
        return
    perintah = parse_perintah(teks)
    if perintah:
        state["menunggu_caption"].pop(chat, None)
        mode_id, jumlah = perintah
        for _ in range(jumlah):
            buat_video(mode_id, chat)
        return
    job = state["menunggu_caption"].pop(chat, None)
    if job and teks:
        revisi_caption(chat, job, teks)
        return
    kirim_teks(chat, BANTUAN)


def tangani_tombol(cq, state):
    from .factory import buat_video, catat_topik
    chat = str(cq["message"]["chat"]["id"])
    if not pemilik() or chat != pemilik():
        return
    try:
        tg("answerCallbackQuery", callback_query_id=cq["id"])
    except Exception:
        pass  # tombol lama: tidak masalah
    aksi, _, job = cq["data"].partition(":")
    p = DATA / "pending" / f"{job}.json"
    pk = load_json(p)
    if not pk:
        kirim_teks(chat, "Data video itu sudah tidak ditemukan (mungkin sudah ditekan sebelumnya).")
        return
    if aksi != "cap":
        try:
            tg("editMessageReplyMarkup", chat_id=chat, message_id=cq["message"]["message_id"], reply_markup={"inline_keyboard": []})
        except Exception:
            pass
    if aksi == "ok":
        catat_topik("disetujui", pk)
        p.unlink(missing_ok=True)
        kirim_teks(chat, f"✅ Disetujui. Topik disimpan ke database dan tidak akan dibuat lagi:\n{pk['topik']}\n\nSilakan upload manual ke TikTok/Reels.")
    elif aksi == "re":
        catat_topik("dibuat_ulang", pk)
        p.unlink(missing_ok=True)
        kirim_teks(chat, "🔄 Membuat ulang dengan topik baru...")
        buat_video(pk["mode"], chat)
    elif aksi == "no":
        catat_topik("dibuang", pk)
        p.unlink(missing_ok=True)
        kirim_teks(chat, "🗑 Dibuang. Mencari topik lain...")
        buat_video(pk["mode"], chat)
    elif aksi == "cap":
        state["menunggu_caption"][chat] = job
        kirim_teks(chat, "✏️ Ketik instruksi revisi caption (contoh: lebih singkat, tambah ajakan komentar, hapus emoji).")


def jalan():
    state = load_json(STATE, {"offset": 0, "menunggu_caption": {}})
    state.setdefault("menunggu_caption", {})
    updates = ambil_update(state)
    if updates:  # tandai "sudah dibaca" di sisi Telegram sekarang juga, supaya tidak pernah diproses dua kali
        state["offset"] = updates[-1]["update_id"] + 1
        save_json(STATE, state)
        tg("getUpdates", offset=state["offset"], limit=1, timeout=0)
    for u in updates:
        try:
            if u.get("message"):
                tangani_pesan(u["message"], state)
            elif u.get("callback_query"):
                tangani_tombol(u["callback_query"], state)
        except Exception:
            log(traceback.format_exc())
            if pemilik():
                kirim_teks(pemilik(), "❌ Terjadi error saat memproses pesan. Coba kirim ulang.")
        save_json(STATE, state)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cek", action="store_true")
    ap.add_argument("--jalan", action="store_true")
    ap.add_argument("--mode", default="")
    ap.add_argument("--jumlah", default="1")
    a = ap.parse_args()
    if a.cek:  # ringan: tidak memuat pustaka video
        cek()
        return
    if a.mode.strip() in ("1", "2", "3") and pemilik():
        from .factory import buat_video
        for _ in range(max(1, min(int(a.jumlah or 1), 3))):
            buat_video(a.mode.strip(), pemilik())
    jalan()


if __name__ == "__main__":
    main()
