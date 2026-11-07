"""Penulis paket kuis, lalu penguji yang menilai dirinya sendiri."""
import json
import random

from .common import gemini_json, load_db, log, mirip

TEMA_GELAR = [
    "hewan nyeleneh dengan kekurangan yang lucu",
    "profesi absurd yang tidak ada di dunia nyata",
    "benda rumah tangga yang punya masalah harga diri",
    "gelar kerajaan konyol dari kerajaan yang tidak jelas",
    "makhluk mitologi yang salah kostum",
    "tokoh sinetron yang dramanya berlebihan",
    "makanan yang punya drama hidup",
    "kendaraan yang mengalami krisis eksistensial",
    "pahlawan super yang gajinya telat",
    "alat kantor yang sedang burnout",
    "planet atau benda langit yang sedang galau",
    "jabatan di organisasi RT yang absurd",
]
ANGKA_KATA = {3: "tiga", 4: "empat", 5: "lima", 6: "enam", 7: "tujuh"}


def riwayat():
    """Soal dan tema gelar yang pernah dibuat/ditolak, supaya tidak diulang."""
    db = load_db()
    soal, tema = [], []
    for kolom in ("disetujui", "dibuang", "dibuat_ulang"):
        for x in db[kolom]:
            soal += x.get("soal", [])
            if x.get("tema"):
                tema.append(x["tema"])
    return soal[-80:], tema[-12:]


def _prompt_tulis(n, tema_saran, soal_pakai, tema_pakai, masukan):
    return f"""Kamu penulis konten kuis viral Indonesia untuk Reels dan TikTok. Buat 1 paket video kuis interaktif.

GAYA HUMOR: nyeleneh, sarkas ringan, absurd, random. Sarkas ditujukan ke situasi sehari-hari (alarm, saldo, deadline, sinyal, cicilan),
BUKAN ke SARA, agama, politik, fisik orang, atau kelompok tertentu. Tanpa kata kasar atau dewasa.

SOAL: tepat {n} soal, urut dari mudah ke susah.
- {n - 3} soal bertipe "logika": teka-teki bernalar, jawabannya pasti dan tunggal.
- 2 soal bertipe "tebakan": tebak-tebakan nyeleneh atau absurd; jawabannya lucu tapi masih masuk akal sehingga penonton bisa menebak.
- soal terakhir bertipe "jebakan": MINDBLOWING. Jawabannya bertentangan dengan intuisi, kebanyakan orang salah, tapi bisa dibuktikan.
Batas panjang: q (soal) maksimal 14 kata; a (jawaban) maksimal 7 kata; a2 (penjelasan satu kalimat yang bikin "oh iya ya!") maksimal 20 kata.
Soal harus ORISINAL: jangan pakai soal klasik yang sangat terkenal (misalnya soal lubang, bulan 28 hari, ayam jantan bertelur, posisi lomba lari).
JAWABAN WAJIB BENAR SECARA LOGIKA dan tidak punya jawaban lain yang sama masuk akal. Jangan mengarang fakta.

GELAR: 4 gelar bertingkat untuk skor {n}/{n}, {n - 1}/{n}, {n - 2}/{n}, dan 0-{n - 3}, urut dari skor tertinggi.
Tema gelar kali ini (boleh dimodifikasi agar lebih lucu): {tema_saran}.
Nama gelar 2-4 kata, tagline maksimal 9 kata, nyeleneh dan membuat orang ingin pamer di komentar.
Gelar skor tertinggi terdengar bangga tapi absurd; gelar skor terendah lucu sampai orang rela mengakuinya.
Tema gelar yang SUDAH DIPAKAI, jangan ulangi: {tema_pakai or 'belum ada'}
Soal yang SUDAH PERNAH dibuat, jangan ulangi atau mirip: {soal_pakai or 'belum ada'}
{('PERBAIKAN WAJIB dari penilaian sebelumnya: ' + masukan) if masukan else ''}

caption: 2-3 kalimat yang mengajak penonton menulis skor dan gelarnya di komentar. hashtag: 6-8 buah. judul_pilihan: 3 judul pendek.

Jawab HANYA JSON:
{{"tema_gelar": "...", "soal": [{{"tipe": "logika|tebakan|jebakan", "q": "...", "a": "...", "a2": "..."}}],
 "gelar": [{{"nama": "...", "tagline": "..."}}], "caption": "...", "hashtag": ["#..."], "judul_pilihan": ["...", "...", "..."]}}"""


def _cek_keras(p, n, soal_pakai):
    m = []
    soal = p.get("soal", [])
    if len(soal) != n:
        m.append(f"jumlah soal {len(soal)}, harus {n}")
        return m
    if len(p.get("gelar", [])) != 4:
        m.append("gelar harus tepat 4")
    for i, s in enumerate(soal, 1):
        for k in ("q", "a", "a2"):
            if not str(s.get(k, "")).strip():
                m.append(f"soal {i} tidak punya '{k}'")
        if len(str(s.get("q", "")).split()) > 18:
            m.append(f"soal {i} terlalu panjang ({len(s['q'].split())} kata, maks 14)")
        if len(str(s.get("a", "")).split()) > 10:
            m.append(f"jawaban soal {i} terlalu panjang")
        if len(str(s.get("a2", "")).split()) > 26:
            m.append(f"penjelasan soal {i} terlalu panjang")
        for lama in soal_pakai:
            if mirip(s.get("q", ""), lama) >= 0.6:
                m.append(f"soal {i} mirip dengan soal lama: {lama[:50]}")
                break
    for i, g in enumerate(p.get("gelar", []), 1):
        if len(str(g.get("nama", "")).split()) > 6 or not str(g.get("nama", "")).strip():
            m.append(f"nama gelar {i} kosong atau terlalu panjang")
        if len(str(g.get("tagline", "")).split()) > 12:
            m.append(f"tagline gelar {i} terlalu panjang")
    return m


def _uji(p):
    """AI penguji: jawaban benar? ambigu? lucu? orisinal?"""
    daftar = [{"no": i, "q": s["q"], "a": s["a"], "a2": s["a2"], "tipe": s.get("tipe")} for i, s in enumerate(p["soal"], 1)]
    h = gemini_json(f"""Kamu penguji kuis yang KRITIS dan jujur. Untuk tiap soal di bawah, selesaikan sendiri soalnya dulu, baru bandingkan dengan kunci jawabannya.
Soal: {json.dumps(daftar, ensure_ascii=False)}
Gelar: {json.dumps(p['gelar'], ensure_ascii=False)}

Untuk tiap soal nilai: jawaban_benar (true jika kunci benar secara logika), ambigu (true jika ada jawaban lain yang sama masuk akal),
lucu (1-10, seberapa nyeleneh/absurd/lucu atau mindblowing), orisinal (1-10; beri rendah kalau soal klasik yang sangat terkenal).
Nilai juga gelar_lucu (1-10) dan aman (false jika ada unsur SARA, politik, menghina fisik/kelompok, atau kata kasar).
Jawab HANYA JSON: {{"soal": [{{"no": 1, "jawaban_benar": true, "ambigu": false, "lucu": 7, "orisinal": 7, "catatan": "..."}}], "gelar_lucu": 7, "aman": true, "saran": "perintah perbaikan singkat"}}""",
                    temperature=0.2)
    return h


def buat_paket(n=5):
    """Mengembalikan (paket, catatan_kualitas). Mengulang sampai 3 kali bila belum lolos uji."""
    soal_pakai, tema_pakai = riwayat()
    sisa = [t for t in TEMA_GELAR if t not in tema_pakai] or TEMA_GELAR
    terbaik, masukan = None, None
    for ke in range(1, 4):
        tema = random.choice(sisa)
        try:
            p = gemini_json(_prompt_tulis(n, tema, soal_pakai, tema_pakai, masukan), temperature=1.0)
            if isinstance(p, list):
                p = p[0]
            keras = _cek_keras(p, n, soal_pakai)
            if keras:
                masukan = "; ".join(keras)
                log(f"[penulis] percobaan {ke} gagal cek: {masukan[:200]}")
                continue
            u = _uji(p)
        except Exception as e:
            log(f"[penulis] percobaan {ke} error: {e}")
            if "Kuota semua model" in str(e):
                raise
            continue
        us = u.get("soal", [])
        salah = [x["no"] for x in us if not x.get("jawaban_benar", True)]
        ambigu = [x["no"] for x in us if x.get("ambigu")]
        lucu = (sum(float(x.get("lucu", 5)) for x in us) / max(1, len(us)) + float(u.get("gelar_lucu", 5))) / 2
        asli = sum(float(x.get("orisinal", 5)) for x in us) / max(1, len(us))
        aman = u.get("aman", True)
        nilai = lucu - 3 * len(salah) - 2 * len(ambigu) - (5 if not aman else 0)
        log(f"[penulis] percobaan {ke}: lucu {lucu:.1f}, orisinal {asli:.1f}, salah {salah}, ambigu {ambigu}, aman {aman}")
        cat = {"lucu": round(lucu, 1), "orisinal": round(asli, 1), "salah": salah, "ambigu": ambigu, "aman": aman}
        if terbaik is None or nilai > terbaik[2]:
            terbaik = (p, cat, nilai)
        if not salah and not ambigu and aman and lucu >= 7 and asli >= 6:
            break
        masukan = (u.get("saran") or "") + (f" Ganti soal nomor {salah + ambigu} karena jawabannya salah atau ambigu." if salah or ambigu else "") \
            + (" Soal/gelar harus lebih lucu dan orisinal." if lucu < 7 or asli < 6 else "") + (" Hapus unsur tidak aman." if not aman else "")
    if terbaik is None:
        raise RuntimeError("Gagal menulis paket kuis yang lengkap. Coba lagi.")
    p, cat, _ = terbaik
    if cat["salah"]:
        raise RuntimeError(f"Penguji menemukan jawaban salah di soal {cat['salah']} setelah 3 kali mencoba. Coba lagi.")
    p["tema_gelar"] = p.get("tema_gelar") or "gelar"
    return p, cat
