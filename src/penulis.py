"""Penulis paket konten untuk 4 jenis: tebak-tebakan, teka-teki, tes logika, tes psikologi. Plus penguji."""
import json
import random

from .common import gemini_json, load_db, log, mirip

JENIS = {
    "tebak": {"nama": "Tebak-tebakan", "pill": "TEBAK-TEBAKAN", "skor": True},
    "teka": {"nama": "Teka-teki", "pill": "TEKA-TEKI", "skor": True},
    "logika": {"nama": "Tes Logika", "pill": "TES LOGIKA", "skor": True},
    "psiko": {"nama": "Tes Psikologi", "pill": "TES PSIKOLOGI", "skor": False},
}
ANGKA_KATA = {1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima", 6: "enam", 7: "tujuh", 8: "delapan"}

DIMENSI = {
    "tebak": ["Kreativitas Berpikir", "Kepekaan Humor", "Cara Pandang Lateral", "Kelincahan Berpikir"],
    "teka": ["Berpikir Lateral", "Ketelitian Membaca Soal", "Kejernihan Penalaran", "Ketajaman Intuisi"],
    "logika": ["Penalaran Logis", "Pengenalan Pola", "Ketelitian Berhitung", "Analisis Cepat"],
}


def riwayat(jenis):
    db = load_db()
    soal, tema = [], []
    for kolom in ("disetujui", "dibuang", "dibuat_ulang"):
        for x in db[kolom]:
            if x.get("jenis", "teka") == jenis:
                soal += x.get("soal", [])
                if x.get("tema"):
                    tema.append(x["tema"])
    return soal[-80:], tema[-10:]


AMAN = ("Aman: tanpa SARA, agama, politik, menghina fisik atau kelompok tertentu, kata kasar, atau unsur dewasa.")

INSTRUKSI = {
    "tebak": """JENIS: TEBAK-TEBAKAN dengan humor nyeleneh, sarkas ringan, absurd, random. Sarkas ditujukan ke situasi sehari-hari (alarm, saldo, deadline, sinyal, cicilan), bukan ke kelompok orang.
Tepat {n} tebakan, urut dari mudah ke susah. q (pertanyaan) maksimal 14 kata. a (jawaban/punchline) maksimal 8 kata: lucu atau absurd tapi masih masuk akal sehingga penonton bisa menebaknya.
a2: satu kalimat tambahan yang menguatkan lucunya, maksimal 18 kata. Jangan pakai tebakan klasik yang sangat terkenal.""",
    "teka": """JENIS: TEKA-TEKI berpikir lateral dan logika dengan jawaban yang bikin 'oh iya ya!' (mindblowing).
Tepat {n} soal, urut dari mudah ke susah. Soal terakhir adalah JEBAKAN: jawabannya bertentangan dengan intuisi, kebanyakan orang salah, tapi bisa dibuktikan.
q maksimal 18 kata. a maksimal 8 kata. a2 (penjelasan satu kalimat) maksimal 24 kata. Jangan pakai soal klasik yang sangat terkenal (lubang, bulan 28 hari, ayam jantan bertelur, posisi lomba lari).
Jawaban harus pasti dan tunggal. Humor boleh sedikit, tapi soalnya bernalar.""",
    "logika": """JENIS: TES LOGIKA yang SERIUS dan adil (tanpa humor di soal). Variasikan tipe: deret angka, penalaran verbal/silogisme, urutan dan perbandingan, hitungan cerdik, pola huruf.
Tepat {n} soal, urut dari mudah ke susah. q maksimal 22 kata. a maksimal 8 kata. a2 = penjelasan langkah penyelesaian maksimal 26 kata.
Setiap soal harus bisa dikerjakan di kepala dalam kurang dari 20 detik oleh orang awam yang teliti, jawabannya pasti dan tunggal. Jangan memakai rumus rumit.""",
    "psiko": """JENIS: TES PSIKOLOGI populer (hiburan, BUKAN diagnosis). Tepat {n} pertanyaan situasi sehari-hari. Tiap pertanyaan punya 3 pilihan A, B, C yang SEIMBANG (tidak ada yang jelas lebih baik atau lebih buruk).
Pertanyaan maksimal 16 kata; tiap pilihan maksimal 10 kata. Pilihan A selalu mencerminkan tipe 1, B tipe 2, C tipe 3, konsisten di semua pertanyaan.
Hasil: 3 tipe kepribadian (untuk yang paling banyak memilih A, B, atau C). Nama tipe 2-4 kata. Deskripsi maksimal 28 kata: bahasa positif tapi jujur, sebut satu kekuatan dan satu hal yang bisa dikembangkan. Tidak menghakimi dan tidak mengklaim diagnosis medis.""",
}

TINGKAT = """TINGKAT PENILAIAN (SERIUS, informatif, memotivasi, TIDAK bercanda dan tidak mengejek): 4 tingkat untuk skor {n}/{n}, {n1}/{n}, {n2}/{n}, dan 0-{n3}, urut dari skor tertinggi.
Dimensi yang dinilai kali ini: {dimensi}. Tiap tingkat punya nama 2-4 kata (contoh bentuk: "Analis Tajam") dan deskripsi maksimal 15 kata yang menjelaskan kemampuan penonton pada tingkat itu.
Tingkat terendah tetap sopan dan memberi semangat (contoh bentuk: "Pemula yang Berpotensi")."""

SKEMA_SKOR = """{"dimensi": "...", "soal": [{"q": "...", "a": "...", "a2": "..."}],
 "tingkat": [{"nama": "...", "deskripsi": "..."}], "caption": "...", "hashtag": ["#..."], "judul_pilihan": ["...", "...", "..."]}"""
SKEMA_PSIKO = """{"soal": [{"q": "...", "opsi": {"A": "...", "B": "...", "C": "..."}}],
 "hasil": [{"huruf": "A", "nama": "...", "deskripsi": "..."}, {"huruf": "B", ...}, {"huruf": "C", ...}],
 "caption": "...", "hashtag": ["#..."], "judul_pilihan": ["...", "...", "..."]}"""


def _prompt(jenis, n, soal_pakai, tema_pakai, dimensi, masukan):
    isi = INSTRUKSI[jenis].format(n=n)
    if JENIS[jenis]["skor"]:
        isi += "\n\n" + TINGKAT.format(n=n, n1=n - 1, n2=n - 2, n3=n - 3, dimensi=dimensi)
        skema = SKEMA_SKOR
    else:
        skema = SKEMA_PSIKO
    return f"""Kamu penulis konten kuis interaktif Indonesia untuk Reels dan TikTok yang memancing penonton berkomentar. {AMAN}

{isi}

Soal yang SUDAH PERNAH dibuat, jangan ulangi atau mirip: {soal_pakai or 'belum ada'}
Dimensi/tema yang sudah dipakai, ganti yang lain: {tema_pakai or 'belum ada'}
{('PERBAIKAN WAJIB dari penilaian sebelumnya: ' + masukan) if masukan else ''}

caption: 2-3 kalimat yang mengajak penonton menulis hasilnya di komentar. hashtag: 6-8. judul_pilihan: 3 judul pendek.
Jawab HANYA JSON:
{skema}"""


def _kata(x):
    return len(str(x).split())


def _cek_keras(p, jenis, n, soal_pakai):
    m = []
    soal = p.get("soal", [])
    if len(soal) != n:
        return [f"jumlah soal {len(soal)}, harus {n}"]
    batas_q = {"tebak": 16, "teka": 22, "logika": 26, "psiko": 20}[jenis]
    for i, s in enumerate(soal, 1):
        if not str(s.get("q", "")).strip():
            m.append(f"soal {i} kosong")
        if _kata(s.get("q", "")) > batas_q:
            m.append(f"soal {i} terlalu panjang ({_kata(s['q'])} kata, maks {batas_q})")
        for lama in soal_pakai:
            if mirip(s.get("q", ""), lama) >= 0.6:
                m.append(f"soal {i} mirip soal lama: {lama[:50]}")
                break
        if jenis == "psiko":
            o = s.get("opsi", {})
            if sorted(o) != ["A", "B", "C"] or any(not str(v).strip() or _kata(v) > 14 for v in o.values()):
                m.append(f"pilihan soal {i} harus A, B, C masing-masing maksimal 14 kata")
        else:
            if not str(s.get("a", "")).strip():
                m.append(f"soal {i} tanpa jawaban")
            if _kata(s.get("a", "")) > 10:
                m.append(f"jawaban soal {i} terlalu panjang")
            if jenis != "tebak" and not str(s.get("a2", "")).strip():
                m.append(f"soal {i} tanpa penjelasan")
            if _kata(s.get("a2", "")) > 30:
                m.append(f"penjelasan soal {i} terlalu panjang")
    if jenis == "psiko":
        h = p.get("hasil", [])
        if sorted(x.get("huruf") for x in h) != ["A", "B", "C"]:
            m.append("hasil harus untuk A, B, C")
        for x in h:
            if not str(x.get("nama", "")).strip() or _kata(x.get("deskripsi", "")) > 36 or not str(x.get("deskripsi", "")).strip():
                m.append(f"hasil {x.get('huruf')} kosong atau deskripsi terlalu panjang")
    else:
        if len(p.get("tingkat", [])) != 4:
            m.append("tingkat harus tepat 4")
        for i, g in enumerate(p.get("tingkat", []), 1):
            if not str(g.get("nama", "")).strip() or _kata(g.get("nama", "")) > 6:
                m.append(f"nama tingkat {i} kosong atau terlalu panjang")
            if not str(g.get("deskripsi", "")).strip() or _kata(g.get("deskripsi", "")) > 20:
                m.append(f"deskripsi tingkat {i} kosong atau terlalu panjang")
    return m


def _uji(p, jenis):
    daftar = json.dumps(p["soal"], ensure_ascii=False)
    if jenis == "psiko":
        isi = f"""Pertanyaan tes psikologi: {daftar}
Hasil: {json.dumps(p['hasil'], ensure_ascii=False)}
Nilai: seimbang (true jika pilihan A/B/C tiap pertanyaan tidak ada yang jelas lebih baik atau buruk), konsisten (true jika A selalu mencerminkan tipe 1, B tipe 2, C tipe 3 sesuai deskripsi hasil),
menghakimi (true jika ada yang merendahkan atau mengklaim diagnosis), seru (1-10: seberapa relatable dan menarik), aman (false jika ada unsur SARA/politik/dewasa).
Jawab HANYA JSON: {{"seimbang": true, "konsisten": true, "menghakimi": false, "seru": 7, "aman": true, "saran": "..."}}"""
    else:
        isi = f"""Soal ({JENIS[jenis]['nama']}): {daftar}
Tingkat penilaian: {json.dumps(p['tingkat'], ensure_ascii=False)}
Untuk tiap soal, selesaikan sendiri dulu, lalu bandingkan dengan kunci. Nilai per soal: jawaban_benar (true jika kunci benar secara logika/matematika), ambigu (true jika ada jawaban lain yang sama masuk akal),
seru (1-10: lucu untuk tebakan, mindblowing untuk teka-teki, menantang tapi adil untuk tes logika), orisinal (1-10; rendah kalau soal klasik terkenal).
Nilai juga: tingkat_serius (true jika deskripsi tingkat serius, tidak bercanda, tidak mengejek) dan aman (false jika ada unsur SARA/politik/dewasa/menghina).
Jawab HANYA JSON: {{"soal": [{{"no": 1, "jawaban_benar": true, "ambigu": false, "seru": 7, "orisinal": 7}}], "tingkat_serius": true, "aman": true, "saran": "perintah perbaikan singkat"}}"""
    return gemini_json("Kamu penguji konten kuis yang KRITIS dan jujur.\n" + isi, temperature=0.2)


def _normalisasi(p, jenis, n):
    p["jenis"] = jenis
    if jenis == "psiko":
        urut = sorted(p["hasil"], key=lambda x: x["huruf"])
        p["baris"] = [{"label": x["huruf"], "nama": x["nama"], "deskripsi": x["deskripsi"]} for x in urut]
        p["tema_gelar"] = "psikologi"
    else:
        lab = [f"{n}/{n}", f"{n - 1}/{n}", f"{n - 2}/{n}", f"0-{n - 3}"]
        p["baris"] = [{"label": lab[i], "nama": g["nama"], "deskripsi": g["deskripsi"]} for i, g in enumerate(p["tingkat"])]
        p["tema_gelar"] = p.get("dimensi") or "penilaian"
    return p


def buat_paket(jenis, n=5):
    """Mengembalikan (paket, kualitas). Mengulang sampai 3 kali bila belum lolos uji."""
    soal_pakai, tema_pakai = riwayat(jenis)
    pilihan = [d for d in DIMENSI.get(jenis, []) if d not in tema_pakai] or DIMENSI.get(jenis, [""])
    terbaik, masukan = None, None
    for ke in range(1, 4):
        dim = random.choice(pilihan)
        try:
            p = gemini_json(_prompt(jenis, n, soal_pakai, tema_pakai, dim, masukan), temperature=1.0)
            if isinstance(p, list):
                p = p[0]
            keras = _cek_keras(p, jenis, n, soal_pakai)
            if keras:
                masukan = "; ".join(keras)
                log(f"[penulis:{jenis}] percobaan {ke} gagal cek: {masukan[:200]}")
                continue
            u = _uji(p, jenis)
        except Exception as e:
            log(f"[penulis:{jenis}] percobaan {ke} error: {e}")
            if "Kuota semua model" in str(e):
                raise
            continue
        if jenis == "psiko":
            masalah = [k for k, bad in (("tidak seimbang", not u.get("seimbang", True)), ("tidak konsisten", not u.get("konsisten", True)),
                                         ("menghakimi", u.get("menghakimi", False)), ("tidak aman", not u.get("aman", True))) if bad]
            seru = float(u.get("seru", 5)); asli = 7.0; salah, ambigu = [], []
        else:
            us = u.get("soal", [])
            salah = [x["no"] for x in us if not x.get("jawaban_benar", True)]
            ambigu = [x["no"] for x in us if x.get("ambigu")]
            seru = sum(float(x.get("seru", 5)) for x in us) / max(1, len(us))
            asli = sum(float(x.get("orisinal", 5)) for x in us) / max(1, len(us))
            masalah = [k for k, bad in (("tingkat tidak serius", not u.get("tingkat_serius", True)), ("tidak aman", not u.get("aman", True))) if bad]
        nilai = seru - 3 * len(salah) - 2 * len(ambigu) - 4 * len(masalah)
        log(f"[penulis:{jenis}] percobaan {ke}: seru {seru:.1f}, orisinal {asli:.1f}, salah {salah}, ambigu {ambigu}, masalah {masalah}")
        kual = {"seru": round(seru, 1), "orisinal": round(asli, 1), "salah": salah, "ambigu": ambigu, "masalah": masalah}
        if terbaik is None or nilai > terbaik[2]:
            terbaik = (p, kual, nilai)
        if not salah and not ambigu and not masalah and seru >= 7 and asli >= 6:
            break
        masukan = (u.get("saran") or "") + (f" Ganti soal nomor {salah + ambigu}: jawabannya salah atau ambigu." if salah or ambigu else "") \
            + (" Perbaiki: " + ", ".join(masalah) + "." if masalah else "") + (" Buat lebih seru dan orisinal." if seru < 7 or asli < 6 else "")
    if terbaik is None:
        raise RuntimeError("Gagal menulis paket yang lengkap. Coba lagi.")
    p, kual, _ = terbaik
    if kual["salah"] or kual["masalah"]:
        raise RuntimeError(f"Penguji masih menemukan masalah ({kual['salah'] or kual['masalah']}) setelah 3 kali mencoba. Coba lagi.")
    return _normalisasi(p, jenis, n), kual
