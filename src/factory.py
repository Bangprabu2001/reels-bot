"""PABRIK KUIS: tulis -> uji -> suara -> render -> kirim."""
import random
import time
import traceback

from .common import DATA, OUT, load_json, log, save_json, sinkron_repo, tambah_db, ROOT
from .penulis import buat_paket
from .render import bikin_thumbnail, render_video, susun_jadwal
from .suara import buat_narasi, susun_audio
from .telegram import kirim_hasil, kirim_teks, menu_markup


def pengaturan():
    cfg = {"jumlah_soal": 5, "hitung_mundur_detik": 4, "durasi_min_detik": 60, "durasi_maks_detik": 90,
           "suara": {"aktif": True, "nama": "id-ID-ArdiNeural", "kecepatan": "+6%", "nada": "+0Hz"},
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


def buat_video(chat_id):
    """Membuat 1 video kuis dan mengirimnya. Mengembalikan job id atau None."""
    tahap = "awal"
    try:
        cfg = pengaturan()
        job = f"{int(time.time())}{random.randint(100, 999)}"
        tahap = "menulis dan menguji soal"
        paket, kual = buat_paket(int(cfg["jumlah_soal"]))
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
        pk = {"job": job, "tema": paket["tema_gelar"], "soal": paket["soal"], "gelar": paket["gelar"], "durasi": jad["total"],
              "kualitas": kual, "caption": paket.get("caption", ""), "hashtag": paket.get("hashtag", []),
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
    tambah_db(kolom, {"judul": pk["soal"][0]["q"], "tema": pk["tema"], "soal": [s["q"] for s in pk["soal"]],
                      "tanggal": time.strftime("%Y-%m-%d")})
