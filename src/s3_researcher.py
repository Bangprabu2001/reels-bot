"""TAHAP 3 - RESEARCHER: riset data asli beserta sumbernya."""
from .common import extract_json, gemini_grounded, gemini_text, log

KHUSUS = {
    "1": """Cari angka NYATA untuk dua jalur hidup yang dibandingkan (harga, cicilan, bunga, biaya bulanan, inflasi/kenaikan harga,
tabungan, kenaikan nilai aset) di Indonesia saat ini. Sertakan asumsi dan rentang angka.""",
    "2": """Cari DALIL dan PENDAPAT ULAMA. Untuk setiap dalil: teks Arab asli (harakat jika ada), terjemah Indonesia, rujukan lengkap
(kitab/hadis, nomor, derajat jika ada). Cantumkan perbedaan pendapat ulama secara adil dengan nama kitabnya. JANGAN mengarang dalil
atau nomor hadis. Kalau tidak menemukan sumber yang jelas, tulis "perlu verifikasi" pada bagian itu.""",
    "3": """Cari angka NYATA usaha ini di Indonesia: modal awal (rincian), margin, volume/omzet, biaya operasional (rincian), laba bersih,
BEP, risiko utama (regulasi, lokasi, dll). Sertakan rentang dan sumbernya. Jangan menebak angka.""",
}


def riset(topik, mode):
    prompt = f"""Kamu RESEARCHER. Topik video: "{topik['judul']}"
Sudut pandang: {topik.get('sudut_baru', '')}

{KHUSUS[mode['id']]}

Gunakan pencarian web. Jawab HANYA dengan JSON (tanpa teks lain) berbentuk:
{{
 "ringkasan": "5-8 kalimat inti temuan",
 "fakta": [{{"klaim": "...", "angka": "angka polos jika ada", "sumber": "nama situs/kitab"}}],
 "angka_kunci": [{{"label": "...", "nilai": 0, "satuan": "..."}}],
 "dalil": [{{"arab": "...", "arti": "...", "rujukan": "..."}}],
 "pendapat": [{{"kitab_atau_ulama": "...", "isi": "..."}}],
 "peringatan": "hal yang belum pasti / perlu dicek manual"
}}
Kosongkan "dalil" dan "pendapat" kalau bukan topik agama."""
    sumber = []
    try:
        teks, sumber = gemini_grounded(prompt)
        data = extract_json(teks)
        data["mode_riset"] = "web"
    except Exception as e:
        log(f"[riset] pencarian web gagal ({e}); pakai pengetahuan AI saja")
        teks = gemini_text(prompt + "\n\nPENCARIAN WEB TIDAK TERSEDIA. Pakai pengetahuanmu, beri angka sebagai perkiraan dan tulis jelas di 'peringatan'.")
        data = extract_json(teks)
        data["mode_riset"] = "tanpa-web"
        data["peringatan"] = "RISET TANPA PENCARIAN WEB, semua angka/dalil WAJIB dicek manual. " + str(data.get("peringatan", ""))
    data["sumber"] = sumber[:8]
    log(f"[riset] selesai ({data['mode_riset']}), {len(sumber)} sumber")
    return data
