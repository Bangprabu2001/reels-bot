"""Uji tampilan tanpa internet dan tanpa kuota: python -m src.demo
Suara diganti hening; soal contoh. Hasil: output/demo/video.mp4"""
import os

os.environ["OFFLINE"] = "1"

from .common import OUT  # noqa: E402
from .factory import pengaturan, produksi  # noqa: E402

DEMO = {
    "tema_gelar": "hewan nyeleneh",
    "soal": [
        {"tipe": "logika", "q": "Ada berapa bulan dalam setahun yang punya 28 hari?", "a": "SEMUA bulan.", "a2": "Februari cuma yang paling pendek, bukan satu-satunya."},
        {"tipe": "tebakan", "q": "Kalau ikan tidur, dia pakai bantal apa?", "a": "Bantal air.", "a2": "Tapi tetap telat bangun, soalnya nggak ada alarm di kolam."},
        {"tipe": "logika", "q": "Aku selalu ada di depanmu, tapi tidak bisa kamu lihat. Apa aku?", "a": "Masa depan.", "a2": "Sering dikhawatirkan, tapi belum pernah kelihatan."},
        {"tipe": "tebakan", "q": "Apa persamaan alarm pagi dan mantan?", "a": "Sama-sama kamu abaikan.", "a2": "Bedanya, alarm masih mau mencoba lagi lima menit kemudian."},
        {"tipe": "jebakan", "q": "3 pil, minum 1 tiap 30 menit. Berapa menit sampai pil habis?", "a": "60 menit, bukan 90!", "a2": "Pil pertama diminum di menit 0."},
    ],
    "gelar": [
        {"nama": "Elang Rabun Bersertifikat", "tagline": "Otak tajam, kacamata ketinggalan."},
        {"nama": "Kancil Telat Mikir", "tagline": "Pintar, tapi loadingnya 3 menit."},
        {"nama": "Siput Pakai Jam Tangan", "tagline": "Tahu waktu, tetap telat."},
        {"nama": "Legenda Salah Terus", "tagline": "Tulis di komentar, kamu tidak sendirian."},
    ],
}

if __name__ == "__main__":
    folder = OUT / "demo"
    folder.mkdir(parents=True, exist_ok=True)
    mp4, thumb, jad, ok, tot = produksi(DEMO, folder, pengaturan())
    print(f"selesai: {mp4} | durasi {jad['total']:.1f} detik | cd {jad['cd']} | catatan: {jad['catatan']}")
