"""PABRIK: menjalankan 7 tahap berurutan untuk 1 video."""
import random
import time
import traceback

from .common import DATA, OUT, load_db, log, save_db, save_json
from .render import bikin_gambar, bikin_suara, bikin_thumbnail, render_video
from .s1_topic_hunter import cari_topik
from .s2_router import kunci_mode
from .s3_researcher import riset
from .s4_s5_story_visual import buat_cerita, buat_visual
from .s6_critique import nilai
from .s7_telegram import kirim_hasil, kirim_teks

MAKS_ULANG = 3


def buat_video(mode_id, chat_id):
    """Menghasilkan 1 video dan mengirimnya ke Telegram. Mengembalikan job_id atau None bila gagal."""
    tahap = "awal"
    try:
        # TAHAP 2 (dikunci lebih dulu supaya semua tahap lain memakai mode yang sama)
        mode = kunci_mode(mode_id)
        job = f"{int(time.time())}{random.randint(100, 999)}"
        kirim_teks(chat_id, f"🏭 MODE {mode['id']} ({mode['nama']}) dimulai.\n"
                            f"Tahap 2 selesai: mode dikunci, rule editing tidak akan tercampur.\nTahap 1: mencari topik...")

        tahap = "1 Topic Hunter"
        topik = cari_topik(mode)
        kirim_teks(chat_id, f"✅ Tahap 1: topik terpilih\n{topik['judul']}\nSudut baru: {topik.get('sudut_baru', '')}\nCek pasaran: {topik['cek_pasaran']}\n\nTahap 3: riset data...")

        tahap = "3 Researcher"
        data = riset(topik, mode)

        tahap = "4-6 Cerita, Visual, Self-Critique"
        terbaik, masukan = None, None
        for ke in range(1, MAKS_ULANG + 1):
            cerita = buat_cerita(topik, mode, data, masukan)
            prompts = buat_visual(cerita, mode, masukan)
            hasil = nilai(cerita, prompts, mode, data)
            if terbaik is None or hasil["skor"] > terbaik[2]["skor"]:
                terbaik = (cerita, prompts, hasil)
            if hasil["skor"] >= 8 and not hasil["keras"]:
                break
            masukan = hasil["saran"]
            kirim_teks(chat_id, f"🔎 Tahap 6: skor {hasil['skor']:g} (di bawah 8), mengulang sendiri ({ke}/{MAKS_ULANG})...")
        cerita, prompts, hasil = terbaik
        kirim_teks(chat_id, f"✅ Tahap 4-6 selesai, skor {hasil['skor']:g}/10.\nTahap 5/7: membuat gambar, suara, dan merakit video (beberapa menit)...")

        tahap = "7 Produksi video"
        folder = OUT / job
        folder.mkdir(parents=True, exist_ok=True)
        seed = random.randint(1, 999999)
        gambar, g_ok = bikin_gambar(prompts, folder, mode, seed)
        wav, batas, kalimat, total, (s_ok, s_total) = bikin_suara(cerita, mode, folder)
        mp4 = render_video(mode, cerita, gambar, batas, kalimat, total, wav, folder / "video.mp4")
        thumb = bikin_thumbnail(mode, cerita, gambar, folder / "thumbnail.jpg")

        catatan = []
        if data.get("peringatan"):
            catatan.append(str(data["peringatan"])[:400])
        if hasil["skor"] < 8:
            catatan.append(f"Skor masih di bawah 8 setelah {MAKS_ULANG} kali ulang. Masalah: " + "; ".join(hasil["masalah"][:4]))
        if g_ok < 4:
            catatan.append(f"Hanya {g_ok} dari 4 gambar berhasil dibuat; sisanya diganti latar polos. Pakai BUAT ULANG.")
        if s_ok < s_total:
            catatan.append(f"Suara AI hanya berhasil {s_ok} dari {s_total} kalimat; video mungkin ada bagian hening.")
        if not (55 <= total <= 95):
            catatan.append(f"Durasi {total:.0f} detik (target sekitar 75).")
        if mode["id"] == "2":
            catatan.append("MODE 2: periksa dalil Arab, arti, dan rujukannya ke kitab/sumber asli sebelum upload.")

        pk = {"job": job, "mode": mode["id"], "topik": topik["judul"], "sudut_baru": topik.get("sudut_baru", ""),
              "skor": hasil["skor"], "judul_pilihan": cerita.get("judul_pilihan") or [topik["judul"]],
              "caption": cerita.get("caption", ""), "hashtag": cerita.get("hashtag", []),
              "sumber": data.get("sumber", []), "catatan": catatan}
        save_json(DATA / "pending" / f"{job}.json", pk)
        kirim_hasil(chat_id, job, pk, mp4, thumb)
        return job
    except Exception as e:
        log(traceback.format_exc())
        kirim_teks(chat_id, f"❌ Pabrik berhenti di tahap {tahap}.\nSebab: {str(e)[:500]}\nKetik MODE {mode_id} lagi untuk mencoba ulang.")
        return None


def catat_topik(kolom, pk):
    db = load_db()
    db[kolom].append({"judul": pk["topik"], "mode": pk["mode"], "tanggal": time.strftime("%Y-%m-%d")})
    save_db(db)
