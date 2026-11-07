"""PABRIK KUIS: tulis -> uji -> suara -> render -> kirim."""
import random
import time
import traceback

from .common import DATA, OUT, load_json, log, save_json, sinkron_repo, tambah_db, ROOT
from .penulis import JENIS, buat_paket
from .render import bikin_thumbnail, render_video, susun_jadwal
from .suara import buat_narasi, susun_audio
from .telegram import kirim_hasil, kirim_teks, menu_markup


def pengaturan():
    cfg = {"jumlah_soal": 5, "waktu_berpikir": {"tebak": 7, "teka": 10, "logika": 12, "psiko": 8}, "tambahan_soal_terakhir": 3,
           "durasi_peringatan_detik": 180,
           "suara": {"aktif": True, "nama": "id-ID-ArdiNeural", "kecepatan": "-12%", "nada": "+0Hz"},
           "musik": {"aktif": True, "file": "assets/musik/latar.mp3", "volume": 0.12}}
    cfg.update(load_json(ROOT / "config" / "pengaturan.json", {}) or {})
    return cfg


def produksi(paket, folder, cfg):
    """Suara -> jadwal -> audio -> video. Dipakai juga oleh demo."""
    klip, dur, s_ok, s_tot = buat_narasi(paket, folder, cfg)
    jad = susun_jadwal(dur, cfg, paket)
    wav = susun_audio(klip, jad, cfg, folder / "audio.wav")
    mp4 = render_video(paket, jad, wav, folder / "video.mp4")
    thumb = None
    try:
        thumb = bikin_thumbnail(paket, jad, folder / "thumbnail.jpg")
    except Exception as e:
        log(f"[thumbnail] dilewati: {e}")
    return mp4, thumb, jad, s_ok, s_tot


def buat_video(chat_id, jenis):
    """Membuat 1 video dari jenis tertentu dan mengirimnya. Mengembalikan job id atau None."""
    tahap = "awal"
    try:
        if jenis not in JENIS:
            jenis = random.choice(list(JENIS))
        cfg = pengaturan()
        job = f"{int(time.time())}{random.randint(100, 999)}"
        tahap = f"menulis dan menguji soal ({JENIS[jenis]['nama']})"
        paket, kual = buat_paket(jenis, int(cfg["jumlah_soal"]))
        tahap = "membuat suara dan video"
        folder = OUT / job
        folder.mkdir(parents=True, exist_ok=True)
        mp4, thumb, jad, s_ok, s_tot = produksi(paket, folder, cfg)

        catatan = []
        if jad.get("catatan"):
            catatan.append(jad["catatan"])
        if cfg["suara"].get("aktif", True) and s_ok < s_tot:
            catatan.append(f"Suara narator hanya berhasil {s_ok} dari {s_tot} bagian; ada bagian hening. Sebaiknya BUAT ULANG.")
        if kual.get("ambigu"):
            catatan.append(f"Soal nomor {kual['ambigu']} dinilai bisa punya lebih dari satu jawaban. Cek dulu sebelum upload.")
        if jenis == "psiko":
            catatan.append("Tes psikologi hanya hiburan, bukan diagnosis. Sudah tertulis di video.")
        pk = {"job": job, "jenis": jenis, "tema": paket.get("tema_gelar", ""), "soal": paket["soal"], "baris": paket["baris"],
              "durasi": jad["total"], "kualitas": kual, "caption": paket.get("caption", ""), "hashtag": paket.get("hashtag", []),
              "judul_pilihan": paket.get("judul_pilihan") or [paket["soal"][0]["q"]], "catatan": catatan}
        save_json(DATA / "pending" / f"{job}.json", pk)
        if not sinkron_repo(f"video {job}"):
            pk["catatan"].append("Data tombol belum tersimpan di GitHub; kalau SETUJU gagal, tekan lagi 1-2 menit kemudian.")
        kirim_hasil(chat_id, job, pk, mp4, thumb)
        return job
    except Exception as e:
        log(traceback.format_exc())
        kirim_teks(chat_id, f"❌ Berhenti saat {tahap}.\nSebab: {str(e)[:500]}\nTekan tombol di bawah untuk mencoba lagi.", menu_markup())
        return None


def catat(kolom, pk):
    tambah_db(kolom, {"judul": pk["soal"][0]["q"], "jenis": pk.get("jenis", "teka"), "tema": pk.get("tema", ""),
                      "soal": [s["q"] for s in pk["soal"]], "tanggal": time.strftime("%Y-%m-%d")})
