"""Dijalankan GitHub Actions saat tombol di Telegram ditekan (lewat Cloudflare Worker).
  python -m src.bot --aksi buat --data tebak:1 --chat 123   -> jenis: tebak | teka | logika | psiko | acak ; angka = jumlah video
  python -m src.bot --aksi ok|re|no --data <job> --chat 123
  python -m src.bot --aksi caption --data "<job>|<instruksi>" --chat 123"""
import argparse
import os
import traceback

from .common import DATA, gemini_json, load_json, log, save_json, sinkron_repo
from .telegram import keyboard, kirim_teks, menu_markup


def revisi_caption(chat, job, instruksi):
    p = DATA / "pending" / f"{job}.json"
    pk = load_json(p)
    if not pk:
        kirim_teks(chat, "⚠️ Data video itu sudah tidak ada (mungkin sudah di-SETUJU/BUANG).", menu_markup())
        return
    h = gemini_json(f"""Revisi caption video kuis ini sesuai permintaan.
Caption lama: {pk['caption']}
Hashtag lama: {' '.join(pk['hashtag'])}
Permintaan revisi: {instruksi}
Jangan mengubah isi soal. Jawab HANYA JSON: {{"caption": "...", "hashtag": ["#..."]}}""", temperature=0.7)
    pk["caption"], pk["hashtag"] = h["caption"], h["hashtag"]
    save_json(p, pk)
    sinkron_repo("revisi caption")
    kirim_teks(chat, "✏️ Caption baru:\n\n" + pk["caption"] + "\n\n" + " ".join(pk["hashtag"]), keyboard(job))


def proses_tombol(aksi, job, chat):
    from .factory import buat_video, catat
    p = DATA / "pending" / f"{job}.json"
    pk = load_json(p)
    if not pk:
        kirim_teks(chat, "⚠️ Data video itu tidak ditemukan (mungkin sudah ditekan sebelumnya, atau belum tersimpan; coba lagi 1 menit lagi).", menu_markup())
        return
    if aksi == "ok":
        catat("disetujui", pk); p.unlink(missing_ok=True); sinkron_repo("kuis disetujui")
        kirim_teks(chat, "✅ Disetujui. Soal dan tema gelar ini tidak akan dibuat lagi.\nSilakan upload manual ke TikTok/Reels.", menu_markup())
    elif aksi == "re":
        catat("dibuat_ulang", pk); p.unlink(missing_ok=True); sinkron_repo("buat ulang")
        kirim_teks(chat, "🔄 Membuat ulang dengan soal baru (±8 menit)...")
        buat_video(chat, pk.get("jenis", "acak"))
    elif aksi == "no":
        catat("dibuang", pk); p.unlink(missing_ok=True); sinkron_repo("kuis dibuang")
        kirim_teks(chat, "🗑 Dibuang. Membuat yang baru (±8 menit)...")
        buat_video(chat, pk.get("jenis", "acak"))


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
        if a.aksi == "buat":
            import random
            from .factory import buat_video
            from .penulis import JENIS
            jenis, _, jml = (a.data or "acak:1").partition(":")
            jml = max(1, min(int(jml or 1), 4))
            urut = random.sample(list(JENIS), jml) if jenis == "acak" and jml <= len(JENIS) else [jenis] * jml
            for j in urut:
                buat_video(chat, j)
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
