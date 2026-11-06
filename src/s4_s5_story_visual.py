"""TAHAP 4 - STORY ARCHITECT dan TAHAP 5 - VISUAL + VOICEOVER (naskah + 4 prompt gambar)."""
import json
import re

from .common import gemini_json, log
from .s2_router import rules_block

SKEMA_UMUM = """{
 "judul_pilihan": ["judul 1", "judul 2", "judul 3"],
 "caption": "caption siap posting, 2-4 kalimat, ada ajakan interaksi",
 "hashtag": ["#..", "#.."],
 "thumbnail_teks": "maks 6 kata, besar dan memancing",
 "karakter": %KARAKTER%,
 "babak": [ 4 objek, urut babak 1..4, tiap objek: {
    "no": 1,
    "voiceover": "naskah yang diucapkan di babak ini",
    "judul_layar": "teks besar di tengah sesaat (boleh kosong)",
    "sorot": ["kata penting untuk di-highlight di subtitle"],
    "angka_melayang": [{"teks": "...", "warna": "merah|hijau|putih", "sisi": "kiri|kanan|tengah"}]%EXTRA_BABAK%
 } ],
 "perhitungan": [{"label": "...", "rumus": "ekspresi angka polos, contoh 15000*300*30 (tanpa titik ribuan, desimal pakai titik)", "hasil": 0}]%EXTRA_ATAS%
}"""

EKSTRA = {
    "1": dict(
        karakter='{"kiri": "deskripsi tetap tokoh kiri (usia, wajah, rambut, baju utama)", "kanan": "deskripsi tetap tokoh kanan"}',
        babak=', "catatan_visual": "props yang berubah di babak ini"',
        atas="",
        aturan="""- Tokoh laki-laki umur 25, gaji sama, kos sama di Babak 1. KIRI = Path A (enak di awal), KANAN = Path B (sakit di awal).
- Babak 1 judul_layar WAJIB 'TAHUN 0 - TITIK AWAL SAMA'. Babak 3 boleh 'TAHUN 5 - MULAI TERLIHAT BEDANYA'. Babak 4 WAJIB 'TAHUN 10 - REUNI'.
- angka_melayang WAJIB ada di babak 2, 3, dan 4 (merah untuk kerugian/hilang, hijau untuk aset/untung). Sisi kiri untuk tokoh kiri, kanan untuk tokoh kanan.
- Voiceover babak 1 WAJIB diawali persis: 'Bayangkan... Dua orang ini...'. Kalimat terakhir babak 4 WAJIB pertanyaan refleksi.
- Semua angka di layar harus punya baris di 'perhitungan' (selisih, total, dll)."""),
    "2": dict(
        karakter='{"utama": "deskripsi tokoh faceless: wajah polos tanpa mata/hidung/mulut, koko putih, peci hitam, sorban"}',
        babak=""", "teks_layar": ["teks besar pendek seperti TIDAK ADA TAMBAHAN"],
    "dalil": null atau {"arab": "teks Arab", "arti": "arti Indonesia", "kata_kunci": ["frasa di arti yang di-highlight"], "rujukan": "kitab/hadis"},
    "kitab": null atau [{"nama": "nama kitab/ulama", "isi": "inti penjelasan maks 20 kata"}, {"nama": "...", "isi": "..."}]""",
        atas="",
        aturan="""- Babak 2 WAJIB berisi 'dalil' (Arab + arti) HANYA dari riset yang bersumber jelas. Jangan mengarang. Kalau riset menulis 'perlu verifikasi', tulis dalil tetap sebatas yang ada dan jangan menambah.
- Babak 3 WAJIB berisi 'kitab' (2 kitab/ulama berdampingan) dengan perbedaan pendapat disampaikan adil tanpa menyalahkan.
- Babak 4 ditutup doa lembut + ajakan belajar lagi, BUKAN ajakan debat. Tidak ada angka melayang (isi []).
- Bahasa lembut dan sopan, tanpa slang kasar, tidak menggurui."""),
    "3": dict(
        karakter='{"utama": "deskripsi tetap 1 tokoh, contoh Pak Budi, kemeja biru, kacamata"}',
        babak=""", "tabel": null atau {"judul": "...", "baris": [["label", "nilai"], ...maks 7 baris]},
    "mitos_realita": null atau {"mitos": "teks pendek", "realita": "teks pendek"},
    "grafik": null atau {"judul": "...", "x_label": "...", "y_label": "...", "x": ["..",".."], "y": [angka, angka], "teks_besar": "contoh: BEP Jadi 70 TAHUN"}""",
        atas=',\n "pov_label": "POV - Kamu Adalah Pemilik [Nama Usaha]"',
        aturan="""- Babak 1 voiceover diawali 'POV: Kamu Adalah Pemilik [Usaha]' dan menampilkan fantasi enak.
- Babak 2 WAJIB ada 'tabel' rincian modal + total. Babak 3 WAJIB ada 'tabel' margin/volume/gross/OPEX/sisa bersih/BEP DAN 'mitos_realita'. Babak 4 WAJIB ada 'grafik' (turun tajam) + 3 risiko di voiceover.
- Hanya 1 karakter. Semua angka di tabel/grafik/voiceover HARUS konsisten dan terdaftar di 'perhitungan' dengan rumus angka polos.
- Skenario penurunan 50% harus dihitung jujur dari angka riset. Kalau usahanya jadi rugi, tulis BEP 'TIDAK PERNAH TERCAPAI', jangan mengarang angka tahun.
- Gunakan kalimat: 'Bayangkan kamu adalah...', 'Ternyata...', 'Ini yang tidak diceritakan orang...'."""),
}


def _kata_target(mode):
    wps = mode["voiceover"]["kata_per_detik"]
    return {b["no"]: int((b["detik"][1] - b["detik"][0]) * wps) for b in mode["babak"]}


def buat_cerita(topik, mode, riset, masukan=None):
    ek = EKSTRA[mode["id"]]
    skema = (SKEMA_UMUM.replace("%KARAKTER%", ek["karakter"]).replace("%EXTRA_BABAK%", ek["babak"])
             .replace("%EXTRA_ATAS%", ek["atas"]))
    kt = _kata_target(mode)
    prompt = f"""Kamu STORY ARCHITECT. Susun cerita video pendek Indonesia.

{rules_block(mode)}

TOPIK: {topik['judul']}
SUDUT BARU: {topik.get('sudut_baru', '')}

DATA RISET ASLI (pakai ini, jangan mengarang angka/dalil):
{json.dumps({k: v for k, v in riset.items() if k != 'mode_riset'}, ensure_ascii=False)[:9000]}

ATURAN KHUSUS MODE {mode['id']}:
{ek['aturan']}

TARGET PANJANG VOICEOVER (jumlah kata, jangan jauh dari ini):
Babak 1: sekitar {kt[1]} kata, Babak 2: {kt[2]} kata, Babak 3: {kt[3]} kata, Babak 4: {kt[4]} kata.
Voiceover = bahasa Indonesia lisan yang enak didengar, kalimat pendek, tiap kalimat diakhiri titik/tanda tanya.
Judul_pilihan: 3 variasi, tiap judul memuat sudut pandang baru.
{('PERBAIKAN WAJIB dari penilaian sebelumnya: ' + masukan) if masukan else ''}

Jawab HANYA JSON dengan bentuk:
{skema}"""
    cerita = gemini_json(prompt, temperature=0.85)
    if isinstance(cerita, list):
        cerita = cerita[0]
    cerita["babak"] = sorted(cerita.get("babak", []), key=lambda b: b.get("no", 0))[:4]
    for i, b in enumerate(cerita["babak"], 1):
        b["no"] = i
    log(f"[cerita] {len(cerita['babak'])} babak, judul: {cerita.get('judul_pilihan', [''])[0]}")
    return cerita


def buat_visual(cerita, mode, masukan=None):
    """Tahap 5: 4 prompt gambar (satu per babak). Gaya mode ditempel otomatis di setiap prompt."""
    petunjuk = {
        "1": """Babak 1: kedua tokoh berdiri bersebelahan tersenyum di depan kos yang sama (komposisi lebar 2 orang).
Babak 2: HANYA tokoh KIRI (Path A), satu orang di tengah frame, full body, komposisi tinggi, bahagia belanja/nongkrong. Latar bersih agar bisa dipotong setengah layar.
Babak 3: HANYA tokoh KANAN (Path B), satu orang di tengah frame, full body, komposisi tinggi, hemat/bawa bekal/capek tapi konsisten.
Babak 4: wide shot kedua tokoh duduk berhadapan di warung kopi lama 10 tahun kemudian; kiri kusam lelah, kanan rapi tenang.""",
        "2": """Semua tokoh faceless. Babak 1: tokoh bertanya, tanda tanya besar di atas kepala. Babak 2: kitab/dokumen pop-up dan tangan pop-up dengan ruang kosong di tengah untuk teks dalil. Babak 3: dua kitab terbuka berdampingan di meja kayu. Babak 4: masjid pop-up, sajadah, lampu gantung, tasbih, suasana tenang.""",
        "3": """Satu tokoh yang sama di semua gambar. Babak 1: fantasi enak (tidur dapat duit, mobil mewah, antre). Babak 2: blueprint/x-ray denah lahan dan potongan bangunan dengan garis ukur dan angka meter. Babak 3: potongan/diagram operasional dengan tokoh melihat tumpukan tagihan, tetap bergaya blueprint. Babak 4: tokoh menatap grafik turun, suasana serius.""",
    }[mode["id"]]
    prompt = f"""Kamu bagian VISUAL. Buat TEPAT 4 prompt gambar bahasa Inggris (satu per babak), sangat deskriptif, untuk model text-to-image.
Karakter tetap (WAJIB diulang di tiap prompt supaya konsisten): {json.dumps(cerita.get('karakter', {}), ensure_ascii=False)}
Isi per babak (voiceover/ringkasan): {json.dumps([{'no': b['no'], 'voiceover': b['voiceover'][:240], 'judul_layar': b.get('judul_layar', ''), 'catatan': b.get('catatan_visual', '')} for b in cerita['babak']], ensure_ascii=False)}
Petunjuk komposisi MODE {mode['id']}:
{petunjuk}
Jangan menulis teks/huruf di dalam gambar (teks dipasang saat editing). Jangan menyebut gaya lain di luar gaya mode ini.
{('PERBAIKAN dari penilaian sebelumnya: ' + masukan) if masukan else ''}
Jawab HANYA JSON: {{"prompt_gambar": ["...", "...", "...", "..."]}}"""
    hasil = gemini_json(prompt, temperature=0.7)
    prompts = hasil["prompt_gambar"] if isinstance(hasil, dict) else hasil
    prompts = [str(p) for p in prompts][:4]
    while len(prompts) < 4:
        prompts.append(prompts[-1])
    # bersihkan kata terlarang lalu tempel gaya mode secara otomatis
    final = []
    for p in prompts:
        for k in mode.get("kata_dilarang_prompt", []):
            p = re.sub(re.escape(k), "", p, flags=re.I)
        final.append(re.sub(r"\s+", " ", p).strip() + ". Style: " + mode["gaya_gambar"])
    return final
