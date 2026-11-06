"""Uji tampilan tanpa internet dan tanpa kuota: python -m src.demo_render 1
Gambar diganti latar warna, suara diganti hening. Gunanya mengecek overlay (split screen, timeline,
tabel, grafik, dalil, letterbox, subtitle) tampil benar."""
import os
import sys

os.environ["OFFLINE"] = "1"

from .common import OUT, cek_perhitungan  # noqa: E402
from .render import bikin_gambar, bikin_suara, bikin_thumbnail, render_video  # noqa: E402
from .s2_router import kunci_mode  # noqa: E402

DEMO = {
    "1": {
        "judul_pilihan": ["Contoh"], "thumbnail_teks": "Siapa Yang Menang?",
        "karakter": {"kiri": "a", "kanan": "b"},
        "babak": [
            {"no": 1, "voiceover": "Bayangkan... Dua orang ini... Gaji mereka sama. Kos mereka sama.", "judul_layar": "TAHUN 0 - TITIK AWAL SAMA", "angka_melayang": []},
            {"no": 2, "voiceover": "Yang kiri memilih enak dulu. Ngontrak, beli HP baru, nongkrong tiap minggu.", "judul_layar": "",
             "angka_melayang": [{"teks": "-Rp 2.000.000 / Bulan HILANG", "warna": "merah", "sisi": "kiri"}, {"teks": "Rp 0", "warna": "merah", "sisi": "kiri"}]},
            {"no": 3, "voiceover": "Yang kanan memilih sakit dulu. Ambil KPR kecil, bawa bekal, menabung.", "judul_layar": "TAHUN 5 - MULAI TERLIHAT BEDANYA",
             "angka_melayang": [{"teks": "+Aset Rp 350.000.000", "warna": "hijau", "sisi": "kanan"}, {"teks": "Rp 120.000.000", "warna": "hijau", "sisi": "kanan"}]},
            {"no": 4, "voiceover": "Sepuluh tahun kemudian mereka bertemu lagi. Nasibnya terbalik. Kamu mau jadi yang kiri atau yang kanan?", "judul_layar": "TAHUN 10 - REUNI",
             "angka_melayang": [{"teks": "Rp 120.000.000", "warna": "hijau", "sisi": "kanan"}]},
        ],
        "perhitungan": [{"label": "sewa", "rumus": "2000000*12*10", "hasil": 240000000}],
    },
    "2": {
        "judul_pilihan": ["Contoh"], "thumbnail_teks": "Boleh Sayyidina?",
        "karakter": {"utama": "x"},
        "babak": [
            {"no": 1, "voiceover": "Bolehkah kita membaca sayyidina di tahiyat?", "judul_layar": "", "teks_layar": []},
            {"no": 2, "voiceover": "Yang dicontohkan Nabi adalah tanpa tambahan. Mari kita lihat dalilnya.", "judul_layar": "",
             "teks_layar": ["TIDAK ADA TAMBAHAN"],
             "dalil": {"arab": "اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ", "arti": "Ya Allah, limpahkanlah shalawat kepada Muhammad dan keluarga Muhammad.", "kata_kunci": ["limpahkanlah shalawat"], "rujukan": "Contoh rujukan, HR. Bukhari"}},
            {"no": 3, "voiceover": "Para ulama menjelaskan dengan adil dari kitab mereka. Ada yang berpendapat boleh, ada yang memilih mengikuti lafaz.", "judul_layar": "",
             "kitab": [{"nama": "Kitab A", "isi": "Penjelasan singkat pendapat pertama."}, {"nama": "Kitab B", "isi": "Penjelasan singkat pendapat kedua."}]},
            {"no": 4, "voiceover": "Jadi dalam ibadah, kita ikut apa yang dicontohkan. Itulah ittiba. Semoga Allah menambah ilmu kita.", "judul_layar": "ITTIBA IBADAH", "teks_layar": ["ITTIBA IBADAH"]},
        ],
        "perhitungan": [],
    },
    "3": {
        "judul_pilihan": ["Contoh"], "thumbnail_teks": "Bos Usaha? Cek Dulu",
        "pov_label": "POV - Kamu Adalah Pemilik Usaha Contoh", "karakter": {"utama": "Pak Budi"},
        "babak": [
            {"no": 1, "voiceover": "POV: Kamu adalah pemilik usaha. Tidur dapat uang.", "judul_layar": "", "sorot": ["uang"]},
            {"no": 2, "voiceover": "Bayangkan kamu adalah pemilik. Ternyata modalnya besar sekali.", "judul_layar": "", "sorot": ["modalnya", "besar"],
             "tabel": {"judul": "Modal Awal", "baris": [["Lahan", "Rp 5.000.000.000"], ["Bangunan", "Rp 3.000.000.000"], ["Peralatan", "Rp 2.000.000.000"], ["Total modal", "Rp 10.000.000.000"]]}},
            {"no": 3, "voiceover": "Margin kecil dan biaya besar. Ini yang tidak diceritakan orang.", "judul_layar": "", "sorot": ["margin", "biaya"],
             "tabel": {"judul": "Hitungan Bulanan", "baris": [["Gross", "Rp 135.000.000"], ["OPEX", "Rp 90.000.000"], ["Sisa bersih", "Rp 45.000.000"], ["BEP", "18 Tahun"]]},
             "mitos_realita": {"mitos": "Untung Besar", "realita": "Untung Bersih Rp 45 Juta / Bulan"}},
            {"no": 4, "voiceover": "Kalau omzet turun lima puluh persen, usaha ini rugi. Ini bukan bisnis cepat kaya.", "judul_layar": "", "sorot": ["rugi"],
             "grafik": {"judul": "Laba Bulanan vs Omzet", "x_label": "Omzet", "y_label": "Laba (juta)", "x": ["100%", "80%", "60%", "50%"], "y": [45, 28, 3, -22], "teks_besar": "BEP TIDAK PERNAH TERCAPAI"}},
        ],
        "perhitungan": [{"label": "gross", "rumus": "15000*300*30", "hasil": 135000000}],
    },
}


def main():
    mode_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    mode = kunci_mode(mode_id)
    cerita = DEMO[mode_id]
    print("cek hitung:", cek_perhitungan(cerita["perhitungan"]) or "OK")
    folder = OUT / f"demo_mode{mode_id}"
    folder.mkdir(parents=True, exist_ok=True)
    gambar, _ = bikin_gambar(["x"] * 4, folder, mode, 1)
    wav, batas, kalimat, total, _ = bikin_suara(cerita, mode, folder)
    print(f"durasi {total:.1f} detik")
    out = render_video(mode, cerita, gambar, batas, kalimat, total, wav, folder / "video.mp4")
    bikin_thumbnail(mode, cerita, gambar, folder / "thumbnail.jpg")
    print("selesai:", out)


if __name__ == "__main__":
    main()
