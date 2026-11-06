"""PABRIK: menjalankan 7 tahap berurutan untuk 1 video."""
import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from .common import DATA, MODEL_TERPAKAI, OUT, log, save_json, sinkron_repo, tambah_db
from .render import bikin_gambar, bikin_suara, bikin_thumbnail, render_video
from .s1_topic_hunter import cari_topik
from .s2_router import kunci_mode
from .s3_researcher import riset
from .s4_s5_story_visual import buat_cerita, buat_visual
from .s6_critique import nilai
from .s7_telegram import kirim_hasil, kirim_teks, menu_markup

MAKS_ULANG = 3


def coba(nama, fn, kali=2):
    """Jalankan fn; kalau gagal ulangi sekali lagi (kecuali kuota habis)."""
    for i in range(kali):
        try:
            return fn()
        except Exception as e:
            log(f"[{nama}] gagal ({i + 1}/{kali}): {e}")
            if i == kali - 1 or "Kuota semua model" in str(e):
                raise
            time.sleep(5)


def buat_video(mode_id, chat_id):
    """Menghasilkan 1 video dan mengirimnya ke Telegram. Mengembalikan job_id atau None bila gagal."""
    tahap = "awal"
    try:
        mode = kunci_mode(mode_id)  # TAHAP 2: dikunci dulu, semua tahap lain memakai mode ini
        job = f"{int(time.time())}{random.randint(100, 999)}"

        tahap = "1 Topic Hunter"
        topik = coba("topik", lambda: cari_topik(mode))

        tahap = "3 Researcher"
        data = coba("riset", lambda: riset(topik, mode))

        tahap = "4-6 Cerita, Visual, Self-Critique"
        terbaik, masukan, galat = None, None, ""
        for ke in range(1, MAKS_ULANG + 1):
            try:
                cerita = buat_cerita(topik, mode, data, masukan)
                prompts = buat_visual(cerita, mode, masukan)
                hasil = nilai(cerita, prompts, mode, data)
            except Exception as e:
                galat = str(e)
                log(f"[tahap 4-6] percobaan {ke} gagal: {e}")
                if "Kuota semua model" in galat:
                    raise
                continue
            if len(cerita.get("babak", [])) != 4:
                masukan = "Cerita WAJIB tepat 4 babak."
                continue
            if terbaik is None or hasil["skor"] > terbaik[2]["skor"]:
                terbaik = (cerita, prompts, hasil)
            if hasil["skor"] >= 8 and not hasil["keras"]:
                break
            masukan = hasil["saran"]
            log(f"[tahap 6] skor {hasil['skor']:g} (<8), mengulang ({ke}/{MAKS_ULANG})")
        if terbaik is None:
            raise RuntimeError("Gagal menyusun cerita yang lengkap. " + galat[:200])
        cerita, prompts, hasil = terbaik

        tahap = "7 Produksi video"
        folder = OUT / job
        folder.mkdir(parents=True, exist_ok=True)
        seed = random.randint(1, 999999)
        with ThreadPoolExecutor(2) as ex:  # gambar dan suara dibuat bersamaan supaya lebih cepat
            fg = ex.submit(bikin_gambar, prompts, folder, mode, seed)
            fs = ex.submit(bikin_suara, cerita, mode, folder)
            gambar, g_ok = fg.result()
            wav, batas, kalimat, total, (s_ok, s_total) = fs.result()
        mp4 = coba("render", lambda: render_video(mode, cerita, gambar, batas, kalimat, total, wav, folder / "video.mp4"))
        try:
            thumb = bikin_thumbnail(mode, cerita, gambar, folder / "thumbnail.jpg")
        except Exception as e:
            log(f"[thumbnail] dilewati: {e}")
            thumb = None

        catatan = []
        if data.get("peringatan"):
            catatan.append(str(data["peringatan"])[:400])
        if hasil["skor"] < 8:
            catatan.append(f"Skor masih di bawah 8 setelah {MAKS_ULANG} kali ulang. Masalah: " + "; ".join(hasil["masalah"][:4]))
        if g_ok < 4:
            catatan.append(f"Hanya {g_ok} dari 4 gambar berhasil dibuat; sisanya diganti latar polos. Sebaiknya BUAT ULANG.")
        if s_ok < s_total:
            catatan.append(f"Suara AI hanya berhasil {s_ok} dari {s_total} kalimat; video mungkin ada bagian hening.")
        if not (55 <= total <= 95):
            catatan.append(f"Durasi {total:.0f} detik (target sekitar 75).")
        if len(MODEL_TERPAKAI) > 1:
            catatan.append("Kuota satu model Gemini habis, pabrik pindah otomatis. Model dipakai: " + ", ".join(MODEL_TERPAKAI))
        if mode["id"] == "2":
            catatan.append("MODE 2: periksa dalil Arab, arti, dan rujukannya ke kitab/sumber asli sebelum upload.")

        pk = {"job": job, "mode": mode["id"], "topik": topik["judul"], "sudut_baru": topik.get("sudut_baru", ""),
              "skor": hasil["skor"], "judul_pilihan": cerita.get("judul_pilihan") or [topik["judul"]],
              "caption": cerita.get("caption", ""), "hashtag": cerita.get("hashtag", []),
              "sumber": data.get("sumber", []), "catatan": catatan}
        save_json(DATA / "pending" / f"{job}.json", pk)
        if not sinkron_repo(f"video {job}"):  # data tombol harus sudah di GitHub sebelum kamu menekan SETUJU
            pk["catatan"].append("Data tombol belum tersimpan di GitHub; kalau SETUJU gagal, tekan lagi 1-2 menit kemudian.")
        kirim_hasil(chat_id, job, pk, mp4, thumb)
        return job
    except Exception as e:
        log(traceback.format_exc())
        kirim_teks(chat_id, f"❌ Pabrik berhenti di tahap {tahap}.\nSebab: {str(e)[:500]}\nTekan tombol di bawah untuk mencoba lagi.",
                   menu_markup())
        return None


def catat_topik(kolom, pk):
    tambah_db(kolom, {"judul": pk["topik"], "mode": pk["mode"], "tanggal": time.strftime("%Y-%m-%d")})
