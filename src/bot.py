"""Dijalankan GitHub Actions saat tombol di Telegram ditekan (lewat Cloudflare Worker).
  python -m src.bot --aksi mode    --data 2        --chat 123   -> bikin 1 video MODE 2
  python -m src.bot --aksi mode    --data 2:3      --chat 123   -> bikin 3 video MODE 2
  python -m src.bot --aksi ok|re|no --data <job>   --chat 123   -> tombol SETUJU / BUAT ULANG / BUANG
  python -m src.bot --aksi caption --data "<job>|<instruksi>" --chat 123"""
import argparse
import os
import traceback

from .common import DATA, gemini_json, load_json, log, save_json, sinkron_repo
from .s7_telegram import keyboard, kirim_teks, menu_markup


def revisi_caption(chat, job, instruksi):
    p = DATA / "pending" / f"{job}.json"
    pk = load_json(p)
    if not pk:
        kirim_teks(chat, "⚠️ Data video itu sudah tidak ada (mungkin sudah di-SETUJU/BUANG).", menu_markup())
        return
    h = gemini_json(f"""Revisi caption video ini sesuai permintaan.
Topik: {pk['topik']}
Caption lama: {pk['caption']}
Hashtag lama: {' '.join(pk['hashtag'])}
Permintaan revisi: {instruksi}
Jangan menambah fakta baru. Jawab HANYA JSON: {{"caption": "...", "hashtag": ["#..."]}}""", temperature=0.7)
    pk["caption"], pk["hashtag"] = h["caption"], h["hashtag"]
    save_json(p, pk)
    sinkron_repo("revisi caption")
    kirim_teks(chat, "✏️ Caption baru:\n\n" + pk["caption"] + "\n\n" + " ".join(pk["hashtag"]), keyboard(job))


def proses_tombol(aksi, job, chat):
    from .factory import buat_video, catat_topik
    p = DATA / "pending" / f"{job}.json"
    pk = load_json(p)
    if not pk:
        kirim_teks(chat, "⚠️ Data video itu tidak ditemukan (mungkin sudah ditekan sebelumnya, atau belum tersimpan; "
                         "coba lagi 1 menit lagi).", menu_markup())
        return
    if aksi == "ok":
        catat_topik("disetujui", pk)
        p.unlink(missing_ok=True)
        sinkron_repo("topik disetujui")
        kirim_teks(chat, f"✅ Disetujui. Topik disimpan dan tidak akan dibuat lagi:\n{pk['topik']}\n\n"
                         "Silakan upload manual ke TikTok/Reels.", menu_markup())
    elif aksi == "re":
        catat_topik("dibuat_ulang", pk)
        p.unlink(missing_ok=True)
        sinkron_repo("buat ulang")
        kirim_teks(chat, "🔄 Membuat ulang dengan topik baru (±10 menit)...")
        buat_video(pk["mode"], chat)
    elif aksi == "no":
        catat_topik("dibuang", pk)
        p.unlink(missing_ok=True)
        sinkron_repo("topik dibuang")
        kirim_teks(chat, "🗑 Dibuang. Mencari topik lain (±10 menit)...")
        buat_video(pk["mode"], chat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aksi", required=True)
    ap.add_argument("--data", default="")
    ap.add_argument("--chat", default="")
    a = ap.parse_args()
    chat = (a.chat or os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
    if not chat:
        raise SystemExit("Chat ID kosong.")
    try:
        if a.aksi == "mode":
            from .factory import buat_video
            mode_id, _, n = a.data.partition(":")
            for _ in range(max(1, min(int(n or 1), 3))):
                buat_video(mode_id.strip(), chat)
        elif a.aksi in ("ok", "re", "no"):
            proses_tombol(a.aksi, a.data.strip(), chat)
        elif a.aksi == "caption":
            job, _, instruksi = a.data.partition("|")
            revisi_caption(chat, job.strip(), instruksi.strip())
        else:
            log(f"aksi tidak dikenal: {a.aksi}")
    except Exception as e:
        log(traceback.format_exc())
        kirim_teks(chat, f"❌ Terjadi error: {str(e)[:400]}", menu_markup())


if __name__ == "__main__":
    main()
