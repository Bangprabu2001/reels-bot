"""Uji tampilan tanpa internet dan tanpa kuota:
  python -m src.demo logika          -> video lengkap output/demo_logika/video.mp4 (suara hening)
  python -m src.demo logika stills   -> hanya gambar contoh layar (cepat)
Jenis: tebak | teka | logika | psiko"""
import os
import sys

os.environ["OFFLINE"] = "1"

from .common import OUT  # noqa: E402
from .factory import pengaturan, produksi  # noqa: E402
from .penulis import _normalisasi  # noqa: E402

DEMO = {
    "tebak": {"soal": [
        {"q": "Kenapa sinyal HP hilang tepat saat kita butuh banget?", "a": "Dia juga butuh me time.", "a2": "Kita saja yang tidak pernah menanyakan kabarnya."},
        {"q": "Kalau ikan tidur, dia pakai bantal apa?", "a": "Bantal air.", "a2": "Tapi tetap telat bangun, soalnya tidak ada alarm di kolam."},
        {"q": "Apa persamaan alarm pagi dan mantan?", "a": "Sama-sama kamu abaikan.", "a2": "Bedanya, alarm masih mau mencoba lagi lima menit kemudian."},
        {"q": "Kenapa saldo selalu habis padahal kita merasa tidak belanja?", "a": "Karena belanjanya diam-diam.", "a2": "Seperti pencuri profesional, tapi pelakunya kita sendiri dan bukti transfernya rapi."},
        {"q": "Apa yang makin dingin makin ditunggu orang?", "a": "Kopi, kalau sedang hemat.", "a2": ""}],
        "tingkat": [{"nama": "Pemikir Super Kreatif", "deskripsi": "Kamu terbiasa melihat jawaban dari sudut yang tidak terduga."},
                    {"nama": "Pemikir Kreatif", "deskripsi": "Cara pandangmu luwes dan cepat menangkap permainan kata."},
                    {"nama": "Pemikir Berkembang", "deskripsi": "Imajinasimu sudah baik dan akan makin tajam dengan latihan."},
                    {"nama": "Pemula yang Berpotensi", "deskripsi": "Teruslah berlatih membaca sudut pandang yang tidak biasa."}], "dimensi": "Kreativitas Berpikir"},
    "teka": {"soal": [
        {"q": "Ada berapa bulan dalam setahun yang punya 28 hari?", "a": "SEMUA bulan.", "a2": "Februari hanya yang paling pendek, bukan satu-satunya."},
        {"q": "Aku selalu ada di depanmu, tapi tidak bisa kamu lihat. Apa aku?", "a": "Masa depan.", "a2": "Sering dikhawatirkan, tapi belum pernah terlihat."},
        {"q": "Lima orang berjabat tangan, masing-masing sekali. Berapa total jabat tangan?", "a": "10 jabat tangan.", "a2": "Bukan 20: tiap jabat tangan dihitung satu kali, yaitu lima kali empat dibagi dua."},
        {"q": "Seorang pengemudi bus melewati tiga halte, di tiap halte naik dua orang dan turun satu. Berapa umur sang pengemudi?", "a": "Umurmu sendiri, jika kamu pengemudinya.", "a2": "Soal ini menguji apakah kamu membaca kalimat pembukanya dengan teliti dan tidak langsung menghitung penumpang."},
        {"q": "3 pil, minum 1 tiap 30 menit. Berapa menit sampai pil habis?", "a": "60 menit, bukan 90!", "a2": "Pil pertama diminum di menit 0."}],
        "tingkat": [{"nama": "Pemikir Lateral Tingkat Tinggi", "deskripsi": "Kamu tidak mudah terjebak asumsi dan teliti membaca soal."},
                    {"nama": "Penalar Teliti", "deskripsi": "Kamu hanya terlewat satu jebakan, penalaranmu sudah kuat."},
                    {"nama": "Pemikir Berkembang", "deskripsi": "Dasar bernalarmu baik; latih ketelitian membaca soal."},
                    {"nama": "Pemula yang Berpotensi", "deskripsi": "Bernalar itu bisa dilatih, mulailah dari soal sederhana."}], "dimensi": "Berpikir Lateral"},
    "logika": {"soal": [
        {"q": "Deret angka: 2, 4, 8, 16, ... Angka berikutnya berapa?", "a": "32", "a2": "Setiap angka dikalikan dua dari angka sebelumnya."},
        {"q": "Semua kucing adalah hewan. Sebagian hewan bisa terbang. Apakah pasti ada kucing yang bisa terbang?", "a": "Tidak pasti.", "a2": "Yang terbang hanya sebagian hewan, belum tentu termasuk kucing."},
        {"q": "Andi lebih tinggi dari Budi. Budi lebih tinggi dari Citra. Siapa yang paling pendek?", "a": "Citra.", "a2": "Urutan tinggi dari atas: Andi, Budi, Citra."},
        {"q": "Sebuah buku dan pensil harganya 11 ribu. Buku lebih mahal 10 ribu daripada pensil. Berapa harga pensil?", "a": "500 rupiah.", "a2": "Pensil 500, buku 10.500, jumlahnya 11.000. Jawaban 1.000 salah karena selisihnya hanya 9.000."},
        {"q": "Pola huruf: A, C, F, J, ... Huruf berikutnya?", "a": "O", "a2": "Lompatannya bertambah satu tiap langkah: plus 2, plus 3, plus 4, lalu plus 5 dari J menjadi O."}],
        "tingkat": [{"nama": "Analis Tajam", "deskripsi": "Pola dan penalaran kamu tangkap dengan cepat dan tepat."},
                    {"nama": "Penalar Andal", "deskripsi": "Logikamu kuat; ketelitian kecil bisa membawamu ke level tertinggi."},
                    {"nama": "Pemikir Berkembang", "deskripsi": "Dasar logikamu baik dan masih sangat bisa ditingkatkan."},
                    {"nama": "Pemula yang Berpotensi", "deskripsi": "Latihan rutin pada pola sederhana akan cepat meningkatkan kemampuanmu."}], "dimensi": "Penalaran Logis"},
    "psiko": {"soal": [
        {"q": "Kamu tiba di pesta yang hampir semua orangnya tidak kamu kenal. Apa yang pertama kamu lakukan?",
         "opsi": {"A": "Mencari wajah yang sudah kukenal", "B": "Langsung berkenalan dengan orang baru", "C": "Mengamati suasana dulu dari pinggir ruangan"}},
        {"q": "Rencana liburanmu mendadak batal. Reaksimu?",
         "opsi": {"A": "Kecewa, lalu mencari rencana pengganti yang sama aman", "B": "Langsung merancang petualangan baru", "C": "Menikmati waktu sendiri di rumah tanpa beban"}},
        {"q": "Saat bekerja dalam kelompok, kamu biasanya berperan sebagai?",
         "opsi": {"A": "Penjaga kerukunan", "B": "Penggerak yang memberi arahan", "C": "Pemikir yang menyusun strategi"}},
        {"q": "Kamu menemukan dompet berisi uang di jalan. Apa yang kamu lakukan?",
         "opsi": {"A": "Menanyakan orang sekitar dan membantu mencari pemiliknya", "B": "Langsung menyerahkan ke pihak berwenang", "C": "Memeriksa isinya dulu untuk menemukan identitas pemilik"}},
        {"q": "Akhir pekan paling ideal bagimu?",
         "opsi": {"A": "Berkumpul dengan keluarga atau sahabat dekat", "B": "Mencoba tempat atau aktivitas yang belum pernah dicoba", "C": "Membaca, menonton, atau mengerjakan hobi sendiri"}}],
        "hasil": [{"huruf": "A", "nama": "Si Penjaga Harmoni", "deskripsi": "Kamu hangat dan setia, nyaman dengan hubungan yang dekat. Belajarlah menyuarakan kebutuhanmu sendiri tanpa merasa tidak enak."},
                  {"huruf": "B", "nama": "Si Penjelajah Berani", "deskripsi": "Kamu energik dan cepat bertindak, selalu mencari pengalaman baru. Beri ruang untuk jeda dan pertimbangan sebelum melangkah."},
                  {"huruf": "C", "nama": "Si Pengamat Reflektif", "deskripsi": "Kamu teliti dan mandiri, kuat dalam berpikir mendalam. Cobalah lebih sering membagikan pikiranmu kepada orang lain."}]},
}

def siapkan(jenis):
    p = DEMO[jenis]
    return _normalisasi(p, jenis, len(p["soal"]))

if __name__ == "__main__":
    jenis = sys.argv[1] if len(sys.argv) > 1 else "logika"
    paket = siapkan(jenis)
    folder = OUT / f"demo_{jenis}"
    folder.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "stills":
        from .render import Perender, susun_jadwal
        from .suara import buat_narasi
        cfg = pengaturan(); klip, dur, _, _ = buat_narasi(paket, folder, cfg); jad = susun_jadwal(dur, cfg, paket)
        pr = Perender(paket, jad); J = jad["soal"]
        waktu = [("hook", 1.5), ("soal", J[3]["s"] + 1.0), ("hitung", J[3]["s"] + J[3]["soal"] + 2.0)]
        if jenis != "psiko":
            waktu += [("jawab", J[3]["s"] + J[3]["soal"] + J[3]["cd"] + 3.5)]
        else:
            waktu += [("pilih", J[2]["s"] + 2.5)]
        waktu += [("reward_awal", jad["reward"] + jad["baris"][jad["urut"][0]] + 0.8), ("reward_akhir", jad["total"] - 1.0)]
        for nama, t in waktu: pr.frame(t).resize((405, 720)).save(f"/tmp/st_{jenis}_{nama}.jpg", quality=88)
        print(f"{jenis}: total {jad['total']:.0f} detik, waktu berpikir {jad['cd']} detik, bagian: {[n for n, _ in waktu]}")
    else:
        mp4, thumb, jad, ok, tot = produksi(paket, folder, pengaturan())
        print(f"selesai: {mp4} | durasi {jad['total']:.1f} detik")
