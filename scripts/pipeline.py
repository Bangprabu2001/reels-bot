"""Pipeline agen (4 gaya video, satu gaya per video):
Naskah + pemilih gaya -> Pemeriksa Fakta -> Suara+Subtitle -> Ilustrator (gambar kartun) -> data/latest.json

Pemakaian:
    pip install -r scripts/requirements.txt
    export GEMINI_API_KEY=...            # wajib
    export POLLINATIONS_API_KEY=...      # opsional: gambar lebih cepat dan tanpa watermark
    python3 scripts/pipeline.py "kenapa langit berwarna biru" 90
        (angka terakhir = durasi target dalam detik; bisa juga lewat env DURASI)
    python3 scripts/pipeline.py          # tanpa topik: ambil dari topik.txt
Setelah itu render: npm run render
"""
import asyncio
import base64
import datetime
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import edge_tts

from llm import tanya_json
import tts
from sfx import buat_sfx, peta_sfx

ROOT = Path(__file__).resolve().parent.parent
VOICE = os.environ.get("VOICE")  # suara edge-tts (cadangan); kosong = ikut gaya video
SUARA = os.environ.get("SUARA") or "auto"  # "auto" = suara sesuai gaya; atau nama suara Gemini TTS
MESIN_SUARA = os.environ.get("MESIN_SUARA") or "gemini"  # "gemini" atau "edge"
JEDA_TTS = float(os.environ.get("JEDA_TTS") or 4)  # detik antar permintaan suara (jatah gratis terbatas)
RATE = os.environ.get("KECEPATAN") or "+6%"  # sedikit lebih cepat terdengar lebih bertenaga
POLLI_KEY = os.environ.get("POLLINATIONS_API_KEY", "").strip()  # opsional: batas lebih longgar, tanpa watermark
MAKS_GAMBAR = int(os.environ.get("MAKS_GAMBAR") or 14)
GAYA_VALID = ["STYLE_HUD_TECH", "STYLE_PAPER_DAKWAH", "STYLE_RETRO_NOIR", "STYLE_CLAY_3D"]
GAYA_ENV = (os.environ.get("GAYA") or "auto").strip()
LATAR_CLAY = ["#E9E6FF", "#D6F0E0", "#FFF4D6"]

# Satu video = SATU gaya (tidak dicampur). Tiap gaya punya template gambar (diadaptasi dari rancangan:
# bendera Midjourney --style/--no diganti kalimat "Avoid"; label teks dibuat lewat kode, bukan oleh AI gambar),
# suara narator, dan berkas musik latar.
GAYA_INFO = {
    "STYLE_HUD_TECH": {
        "template": (
            "Minimalist neon white line art on pure black background, HUD sci-fi interface, {desc}, "
            "thin glowing monoline icon drawn with 2px white lines, subtle cyan outer glow, dark mode infographic, "
            "cyberpunk medical UI, 9:16 vertical. Avoid: photorealistic, solid fills, 3d render, cartoon, "
            "paper texture, messy background, colorful, text, letters, labels"
        ),
        "suara": "Charon", "edge": "id-ID-ArdiNeural", "musik": "musik_hud.mp3",
        "baca": "Read the following in Indonesian as a deep, calm, mysterious male science-documentary narrator. Measured pace, clear pronunciation, subtle intensity:\n\n",
    },
    "STYLE_PAPER_DAKWAH": {
        "template": (
            "Paper-cut scrapbook illustration, warm cream paper texture background, cute black stickman character "
            "with round head and no face, soft pastel watercolor paper cutout elements of {desc}, washi tape decoration, "
            "drop shadow, hand-drawn doodle style, Islamic aesthetic, cozy and calm, stop motion paper feel, 9:16 vertical. "
            "Avoid: neon, glowing lines, HUD, sci-fi, dark mode, 3d clay, photorealistic, scary, text, letters"
        ),
        "suara": "Sulafat", "edge": "id-ID-GadisNeural", "musik": "musik_paper.mp3",
        "baca": "Read the following in Indonesian with a gentle, warm, comforting tone, like a kind storyteller sharing advice. Slow-medium pace, soft and sincere:\n\n",
    },
    "STYLE_RETRO_NOIR": {
        "template": (
            "Grainy retro noir halftone comic illustration, old newspaper texture, high contrast black and white "
            "photocopy style illustration of {desc}, single red accent color, dramatic ink bleed, halftone dots, "
            "investigative documentary style, vintage historical aesthetic, 9:16 vertical. "
            "Avoid: colorful pastel, cute chibi, neon glow, clean modern, clay 3d, scrapbook cute, text, letters"
        ),
        "suara": "Algenib", "edge": "id-ID-ArdiNeural", "musik": "musik_noir.mp3",
        "baca": "Read the following in Indonesian in a low, dramatic, tense voice like an investigative history documentary. Slow pace with serious emphasis:\n\n",
    },
    "STYLE_CLAY_3D": {
        "template": (
            "Soft clay 3d isometric diorama, cute chibi jelly clay render of {desc}, pastel clean background, "
            "soft studio lighting, matte plasticine material, minimal premium, kawaii 3d, 9:16 vertical. "
            "Avoid: line art, paper texture, halftone, grainy, dark mode, HUD, photorealistic human, scary, text, letters"
        ),
        "suara": "Puck", "edge": "id-ID-GadisNeural", "musik": "musik_clay.mp3",
        "baca": "Read the following in Indonesian in a cheerful, playful, friendly voice, like explaining something fun to a friend. Lively pace, clear pronunciation:\n\n",
    },
}
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "").strip()
UA = {"User-Agent": "reels-bot"}
ALLOWED = {
    "hook", "pertanyaan", "cerita", "bar_chart", "list", "big_number", "compare",
    "timeline", "fakta", "mitos_fakta", "outro",
}

SKEMA = """Jenis scene yang boleh dipakai (semuanya wajib punya "gambar"):
- {"type":"hook","durasi":3,"narasi":"...","teks":"kalimat pendek; kata penting diapit *bintang*"}
- {"type":"pertanyaan","durasi":4,"narasi":"...","teks":"pertanyaan pemancing rasa ingin tahu; kata penting diapit *bintang*"}
- {"type":"cerita","durasi":6,"narasi":"...","kunci":"istilah kunci 1-4 kata","stiker":"satu emoji"}   (narasi di atas ilustrasi; subtitle tampil di tengah layar)
- {"type":"fakta","durasi":4,"narasi":"...","teks":"pernyataan singkat; kata penting diapit *bintang*","ikon":"satu emoji"}
- {"type":"mitos_fakta","durasi":7,"narasi":"...","mitos":"anggapan keliru (singkat)","fakta":"yang benar (singkat)"}
- {"type":"big_number","durasi":6,"narasi":"...","judul":"...","angka":0,"satuan":"...","keterangan":"..."}
- {"type":"bar_chart","durasi":6,"narasi":"...","judul":"...","satuan":"...","data":[{"label":"...","nilai":0}]}
- {"type":"compare","durasi":8,"narasi":"...","judul":"...","kiri":{"nama":"...","poin":["..."]},"kanan":{"nama":"...","poin":["..."]}}
- {"type":"timeline","durasi":8,"narasi":"...","judul":"...","langkah":[{"label":"...","teks":"..."}]}
- {"type":"list","durasi":7,"narasi":"...","judul":"...","poin":[{"ikon":"satu emoji","teks":"..."}]}
- {"type":"outro","durasi":4,"narasi":"...","teks":"ajakan singkat; kata penting diapit *bintang*"}
Field umum: "gambar" = deskripsi SINGKAT bahasa Inggris tentang apa yang digambar untuk scene itu; "label" = tag data dekoratif (hanya untuk STYLE_HUD_TECH, selain itu isi "")."""


PANDUAN_GAYA = """Pilih SATU gaya visual untuk seluruh video berdasarkan topik. DILARANG mencampur gaya.
- "STYLE_HUD_TECH" (futuristik, ilmiah, misterius, gelap): topik Sains, Otak, Tidur, Psikologi, Teknologi, Fakta Medis, Self-Improvement, Neuroscience, Data.
- "STYLE_PAPER_DAKWAH" (hangat, adem, humanis, islami): topik Dakwah, Parenting Ala Quran, Adab, Akhlak, Kisah Keluarga, Nasehat, Edukasi Anak Islami.
- "STYLE_RETRO_NOIR" (historis, investigatif, serius, misteri): topik Sejarah Islam, Sirah Nabawiyah, Konspirasi, True Story, Kisah Perang, Misteri Sejarah.
- "STYLE_CLAY_3D" (modern, premium, ceria, lucu): topik Keuangan, Bisnis, Produktivitas, Habit, Edukasi Modern, Teknologi Finansial.
Jika topik tidak tercantum, pilih gaya yang paling dekat dengan isi dan nadanya."""


def sys_naskah(durasi: int, paksa: str = "") -> str:
    kata = int(durasi * 2.4)
    n = max(6, round(durasi / 6))
    bagian_gaya = (
        f'Gaya video sudah ditentukan: "{paksa}". Isi field "gaya" dengan nilai itu dan tulis naskah sesuai nadanya.'
        if paksa
        else PANDUAN_GAYA
    )
    return f"""Kamu Agen Naskah untuk video pendek (Reels/Shorts) berbahasa Indonesia, ritme cepat.
Balas HANYA JSON valid berbentuk {{"gaya":"STYLE_...","unggah":{{"judul":"...","deskripsi":"...","hashtag":["#..."]}},"scenes":[...]}}.
{bagian_gaya}
Nada naskah mengikuti gaya: HUD = tenang, ilmiah, sedikit misterius; PAPER = hangat, lembut, menyejukkan, menasehati tanpa menggurui; NOIR = dramatis, serius, investigatif, penuh ketegangan; CLAY = ceria, ringan, ramah, modern.
"unggah" = bahan untuk diunggah: judul menarik maksimal 70 karakter, deskripsi 1-2 kalimat, 5-8 hashtag.
{SKEMA}
Aturan:
- Target total sekitar {durasi} detik: seluruh narasi sekitar {kata} kata, sekitar {n} scene PENDEK (4-8 detik tiap scene). Lebih baik banyak scene pendek daripada sedikit scene panjang.
- Narasi maksimal 22 kata per scene. Kalimat pendek, lisan, natural. Jangan menyebut kata "scene".
- Struktur: hook (scene pertama, kalimat pemancing yang kuat) -> konteks singkat -> 3-5 bagian isi yang membahas topik sampai tuntas (jelaskan sebab-akibat, bukan sekadar daftar) -> ringkasan -> outro (scene terakhir).
- Komposisi: sekitar 60% scene bertipe "cerita" (narasi di atas ilustrasi, boleh 2-3 berturut-turut), selingi dengan "fakta", "mitos_fakta", "big_number", "bar_chart", "compare", "timeline", atau "list" hanya bila ada data atau poin yang cocok. Hook di awal, outro di akhir.
- Untuk scene "cerita": isi "kunci" (istilah kunci 1-4 kata, bahasa Indonesia, tampil sebagai label tebal) pada sekitar 60% scene cerita, dan "stiker" (satu emoji yang relevan) pada sekitar 40%. Pakai "pertanyaan" untuk hook atau jeda yang memancing rasa ingin tahu (maksimal 2 per video).
- Hanya fakta yang kamu yakin akurat; angka boleh dibulatkan; jangan mengarang statistik atau sumber.
- "gambar": untuk SETIAP scene, deskripsi SINGKAT (4-12 kata, bahasa Inggris) tentang hal NYATA dan LITERAL yang disebut narasi, dengan satu subjek utama yang jelas (contoh: "a sleeping man in a bed, moon in the window", "a cheetah running"). JANGAN menyebut gaya visual (gaya ditambahkan otomatis), JANGAN metafora atau konsep abstrak, dan hindari teks, angka, grafik, logo. Sesuaikan dengan gaya: HUD = objek yang bisa digambar sebagai ikon garis tipis (otak, bulan, jam, jantung, tempat tidur); CLAY = benda atau adegan lucu yang mudah dibentuk dari tanah liat (koin, celengan, jam, buku); PAPER dan NOIR = siluet, bangunan (masjid), benda, alam. Untuk topik islami (PAPER dan NOIR), DILARANG menggambarkan Nabi, Rasul, sahabat, malaikat, atau sosok suci; pakai siluet tanpa wajah, bangunan, benda, atau alam.
- "label" (hanya untuk STYLE_HUD_TECH): tag dekoratif huruf besar gaya kode, 1-3 kata dipisah garis bawah (contoh: SLEEP_CYCLE, CORTISOL_DIP). JANGAN mengarang angka atau persentase statistik; angka hanya boleh bila memang fakta yang disebut di narasi. Untuk gaya lain isi "".
- Batas: bar_chart maksimal 5 batang, list maksimal 4 poin, compare maksimal 3 poin per sisi, timeline maksimal 4 langkah; teks di layar singkat.
- Pastikan JSON valid: di dalam teks JANGAN memakai tanda kutip ganda (gunakan kutip tunggal atau tanpa kutip), tanpa koma berlebih, tanpa komentar."""


SYS_FAKTA = f"""Kamu Agen Pemeriksa Fakta. Kamu menerima naskah video JSON.
Periksa setiap klaim dan angka. Perbaiki yang salah atau meragukan, ganti dengan versi yang lebih aman (misalnya pembulatan atau kata 'sekitar').
Pertahankan struktur, urutan scene, field "gaya", dan semua field (termasuk "gambar" dan "label") kecuali yang perlu diperbaiki.
Pastikan JSON valid: di dalam teks jangan memakai tanda kutip ganda (gunakan kutip tunggal), tanpa koma berlebih.
Balas HANYA JSON valid dengan bentuk {{"gaya":"...","unggah":{{...}},"scenes":[...]}} (pertahankan field "gaya" dan "unggah"), ditambah field
"catatan_fakta": daftar string singkat tentang hal yang perlu dicek manusia (kosongkan jika tidak ada).
{SKEMA}"""

SYS_KURATOR = """Kamu Agen Kurator Footage untuk video edukasi vertikal. Kamu menerima beberapa scene. Tiap scene punya narasi dan beberapa gambar cuplikan (thumbnail) video stok berlabel "Scene X - Gambar Y".
Untuk SETIAP scene, pilih satu gambar yang paling cocok sebagai video latar untuk narasinya.
Pilih hanya jika isi gambar benar-benar sesuai dengan tema dan narasi (objek, hewan, tempat, atau suasana yang disebut jelas terlihat).
Beri nomor 0 jika semua gambar pada scene itu generik, tidak nyambung, memuat teks/logo/watermark yang mencolok, atau menampilkan orang yang tidak relevan.
Lebih baik 0 daripada footage yang salah.
Balas HANYA JSON: {"pilihan":[{"scene":<nomor scene>,"nomor":<nomor gambar atau 0>,"alasan":"<satu kalimat>"}]} dan sertakan semua scene."""


def validasi(n: dict) -> dict:
    scenes = n.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise SystemExit("Naskah kosong atau bentuknya salah.")
    if scenes[0].get("type") != "hook":
        raise SystemExit("Scene pertama harus hook.")
    for s in scenes:
        t = s.get("type")
        if t not in ALLOWED:
            raise SystemExit(f"Tipe scene tidak dikenal: {t}")
        if not str(s.get("narasi", "")).strip():
            raise SystemExit("Ada scene tanpa narasi.")
        if t == "bar_chart":
            s["data"] = s["data"][:5]
        elif t == "list":
            s["poin"] = s["poin"][:4]
        elif t == "compare":
            for sisi in ("kiri", "kanan"):
                s[sisi]["poin"] = s[sisi]["poin"][:3]
        elif t == "timeline":
            s["langkah"] = s["langkah"][:4]
        elif t == "pertanyaan":
            s["teks"] = str(s.get("teks") or s["narasi"]).strip()
        elif t == "fakta":
            s["ikon"] = str(s.get("ikon") or "💡")
        elif t == "mitos_fakta":
            if not s.get("mitos") or not s.get("fakta"):
                raise SystemExit("Scene mitos_fakta harus punya 'mitos' dan 'fakta'.")
        elif t == "big_number":
            try:
                s["angka"] = float(s["angka"])
            except (TypeError, ValueError, KeyError):
                raise SystemExit("Angka pada scene big_number tidak valid.")
            if s["angka"].is_integer():
                s["angka"] = int(s["angka"])
        s["gambar"] = str(s.get("gambar") or "").strip()[:300]
        s["label"] = re.sub(r"[^A-Za-z0-9_%:. -]", "", str(s.get("label") or "")).strip().upper()[:36]
        s["kunci"] = str(s.get("kunci") or "").strip()[:40]
        s["stiker"] = str(s.get("stiker") or "").strip()[:8]
        b = s.get("broll")
        if isinstance(b, str):
            b = [b]
        s["broll"] = [str(x).strip() for x in (b or []) if str(x).strip()][:3]
    if scenes[-1].get("type") != "outro":
        scenes.append(
            {
                "type": "outro",
                "durasi": 4,
                "gambar": "",
                "broll": [],
                "narasi": "Ikuti untuk fakta seru lainnya!",
                "teks": "Ikuti untuk fakta *seru* lainnya!",
            }
        )
    g = str(n.get("gaya") or "").strip()
    n["gaya"] = g if g in GAYA_VALID else "STYLE_HUD_TECH"
    if n["gaya"] != "STYLE_HUD_TECH":
        for s in scenes:
            s["label"] = ""  # label data hanya dipakai gaya HUD
    u = n.get("unggah") if isinstance(n.get("unggah"), dict) else {}
    tag = u.get("hashtag") or []
    n["unggah"] = {
        "judul": str(u.get("judul") or "").strip()[:100],
        "deskripsi": str(u.get("deskripsi") or "").strip(),
        "hashtag": [str(x).strip() for x in tag if str(x).strip()][:10],
    }
    return n


def agen_naskah(topik: str, durasi: int, paksa: str = "") -> dict:
    return validasi(tanya_json(sys_naskah(durasi, paksa), f"Topik: {topik}"))


def agen_fakta(naskah: dict, topik: str) -> dict:
    hasil = tanya_json(SYS_FAKTA, f"Topik: {topik}\n\nNaskah:\n{json.dumps(naskah, ensure_ascii=False)}")
    return validasi(hasil)


async def sintesis(teks: str, path: Path, voice: str) -> list:
    try:
        comm = edge_tts.Communicate(teks, voice, rate=RATE, boundary="WordBoundary")
    except TypeError:  # edge-tts versi lama: default-nya sudah WordBoundary
        comm = edge_tts.Communicate(teks, voice, rate=RATE)
    kata = []
    with open(path, "wb") as f:
        async for c in comm.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                mulai = c["offset"] / 1e7
                kata.append(
                    {
                        "teks": c["text"],
                        "mulai": round(mulai, 2),
                        "selesai": round(mulai + c["duration"] / 1e7, 2),
                    }
                )
    return kata


def _suara_gemini(naskah: dict, folder: Path, slug: str) -> None:
    info = GAYA_INFO[naskah["gaya"]]
    voice = info["suara"] if SUARA.lower() == "auto" else SUARA
    print(f"  suara: Gemini TTS ({voice}), gaya baca sesuai {naskah['gaya']}")
    for i, s in enumerate(naskah["scenes"]):
        durasi = tts.sintesis(s["narasi"], voice, folder / f"scene_{i}.wav", info["baca"])
        s["audioSrc"] = f"audio/{slug}/scene_{i}.wav"
        s["kata"] = tts.taksir_kata(s["narasi"], durasi)
        s["durasi"] = round(durasi + 0.35, 2)  # sedikit jeda napas di akhir scene
        print(f"  scene {i} ({s['type']}): {s['durasi']} detik")
        time.sleep(JEDA_TTS)


async def agen_suara(naskah: dict, slug: str) -> dict:
    folder = siapkan_folder(ROOT / "public" / "audio" / slug)
    if MESIN_SUARA == "gemini":
        try:
            await asyncio.get_running_loop().run_in_executor(None, _suara_gemini, naskah, folder, slug)
            print(f"  total video: {round(sum(s['durasi'] for s in naskah['scenes']))} detik")
            return naskah
        except Exception as e:
            print(f"  Gemini TTS gagal ({e}). Memakai suara cadangan (edge-tts)...")
    voice_edge = VOICE or GAYA_INFO[naskah["gaya"]]["edge"]
    print(f"  suara: edge-tts ({voice_edge})")
    for i, s in enumerate(naskah["scenes"]):
        file = folder / f"scene_{i}.mp3"
        kata = await sintesis(s["narasi"], file, voice_edge)
        s["audioSrc"] = f"audio/{slug}/scene_{i}.mp3"
        s["kata"] = kata
        # durasi scene = akhir kata terakhir + jeda napas
        s["durasi"] = round((kata[-1]["selesai"] + 0.6) if kata else max(2.5, len(s["narasi"]) / 14), 2)
        print(f"  scene {i} ({s['type']}): {s['durasi']} detik")
    print(f"  total video: {round(sum(s['durasi'] for s in naskah['scenes']))} detik")
    return naskah


def siapkan_folder(path: Path) -> Path:
    """Buat folder. Kalau di jalurnya ada FILE bernama sama (mis. 'public' tidak sengaja berupa file),
    file itu disingkirkan di sesi ini supaya folder bisa dibuat (repo asli tidak berubah)."""
    jalur = []
    p = path
    while p != ROOT and p != p.parent:
        jalur.append(p)
        p = p.parent
    for q in reversed(jalur):
        if q.exists() and not q.is_dir():
            print(f"  peringatan: '{q.relative_to(ROOT)}' di repo berupa FILE, bukan folder. "
                  f"Diabaikan di sesi ini; sebaiknya hapus file itu dari repo.")
            q.unlink()
        q.mkdir(exist_ok=True)
    return path


# ---------------------------------------------------------------- B-roll

def _json(url: str, headers=None) -> dict:
    req = urllib.request.Request(url, headers=headers or UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _varian_pixabay(hit: dict):
    """Pilih file video Pixabay: resolusi terbesar yang ukurannya masih wajar."""
    vids = hit.get("videos") or {}
    ada = [vids[k] for k in ("large", "medium", "small", "tiny") if (vids.get(k) or {}).get("url")]
    if not ada:
        return None
    portrait = ada[0].get("height", 0) > ada[0].get("width", 0)
    bagus = [
        v
        for v in ada
        if (v.get("size") or 0) <= 35_000_000
        and ((v.get("width", 0) >= 540) if portrait else (v.get("height", 0) >= 720))
    ]
    return bagus[0] if bagus else None


def _thumb_pixabay(hit: dict, v: dict) -> str:
    if v.get("thumbnail"):
        return v["thumbnail"]
    for x in (hit.get("videos") or {}).values():
        if (x or {}).get("thumbnail"):
            return x["thumbnail"]
    if hit.get("picture_id"):
        return f"https://i.vimeocdn.com/video/{hit['picture_id']}_640x360.jpg"
    return ""


def kandidat_pixabay(query: str, dipakai: set) -> list:
    """Kumpulkan kandidat video dari Pixabay (portrait lebih dulu, lalu umum)."""
    hasil: dict = {}
    for tinggi_min in (1280, 0):
        param = {
            "key": PIXABAY_KEY,
            "q": query[:100],
            "video_type": "all",
            "per_page": 15,
            "safesearch": "true",
        }
        if tinggi_min:
            param["min_height"] = tinggi_min
        data = _json("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(param))
        for h in data.get("hits", []):
            if h.get("id") in dipakai or h.get("id") in hasil:
                continue
            v = _varian_pixabay(h)
            if not v:
                continue
            hasil[h["id"]] = {
                "id": h["id"],
                "link": v["url"],
                "thumb": _thumb_pixabay(h, v),
                "durasi": h.get("duration", 0),
                "pembuat": h.get("user", "?"),
                "tags": (h.get("tags") or "").lower(),
                "portrait": v.get("height", 0) > v.get("width", 0),
            }
    return list(hasil.values())


def kandidat_pexels(query: str, dipakai: set) -> list:
    """Kumpulkan kandidat video dari Pexels (cadangan bila tidak ada kunci Pixabay)."""
    hasil: dict = {}
    for orientasi in ("portrait", None):
        param = {"query": query, "per_page": 12}
        if orientasi:
            param["orientation"] = orientasi
        data = _json(
            "https://api.pexels.com/videos/search?" + urllib.parse.urlencode(param),
            {"Authorization": PEXELS_KEY, **UA},
        )
        for v in data.get("videos", []):
            if v.get("id") in dipakai or v.get("id") in hasil:
                continue
            files = [
                f
                for f in v.get("video_files", [])
                if f.get("file_type") == "video/mp4" and (f.get("width") or 0) >= 540
            ]
            if not files:
                continue
            f = min(files, key=lambda f: abs(f["width"] - 720))
            hasil[v["id"]] = {
                "id": v["id"],
                "link": f["link"],
                "thumb": v.get("image", ""),
                "durasi": v.get("duration", 0),
                "pembuat": (v.get("user") or {}).get("name", "?"),
                "tags": (v.get("url") or "").lower(),  # alamat halaman memuat kata judul
                "portrait": (f.get("height") or 0) > (f.get("width") or 0),
            }
    return list(hasil.values())


def _kata(teks: str) -> set:
    return set(re.findall(r"[a-z]{3,}", teks.lower()))


def peringkat(kands: list, queries: list, min_detik: float, batas: int = 6) -> list:
    """Urutkan kandidat: tag cocok dengan kata kunci, cukup panjang, lalu portrait."""
    kunci = set()
    for q in queries:
        kunci |= _kata(q)

    def skor(k):
        return (len(kunci & _kata(k["tags"])), k["durasi"] >= min_detik, k["portrait"])

    return sorted(kands, key=skor, reverse=True)[:batas]


def _ambil_gambar(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read(4_000_000)
    return base64.b64encode(data).decode()


def kurator_batch(topik: str, tugas: list) -> dict:
    """Agen Kurator: satu permintaan Gemini untuk SEMUA scene (hemat jatah gratis).
    tugas = [{"i": nomor_scene, "narasi": str, "kands": [kandidat dengan "_gambar"]}]
    Hasil: {nomor_scene: kandidat terpilih}. Scene tanpa pilihan yang cocok tidak dimasukkan."""
    gambar = []
    baris = [f"Tema video: {topik}", "Daftar scene:"]
    for tg in tugas:
        baris.append(f'- Scene {tg["i"]}: "{tg["narasi"]}" (gambar kandidat 1-{len(tg["kands"])})')
        for n, k in enumerate(tg["kands"], 1):
            gambar.append((f'Scene {tg["i"]} - Gambar {n}:', k["_gambar"]))
    try:
        hasil = tanya_json(SYS_KURATOR, "\n".join(baris), gambar, ronde=2)
    except SystemExit as e:  # lebih baik tanpa footage daripada footage salah
        print(f"  kurator gagal ({e}), semua scene memakai latar biasa")
        return {}
    daftar = hasil.get("pilihan", []) if isinstance(hasil, dict) else []
    pilih: dict = {}
    for item in daftar if isinstance(daftar, list) else []:
        try:
            i, n = int(item.get("scene")), int(item.get("nomor", 0))
        except (TypeError, ValueError, AttributeError):
            continue
        tg = next((x for x in tugas if x["i"] == i), None)
        print(f"  kurator scene {i}: pilihan {n} - {item.get('alasan', '')}")
        if tg and 1 <= n <= len(tg["kands"]):
            pilih[i] = tg["kands"][n - 1]
    return pilih


def unduh(link: str, path: Path) -> None:
    req = urllib.request.Request(link, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        shutil.copyfileobj(r, f)


def agen_broll(naskah: dict, slug: str, topik: str) -> dict:
    if PIXABAY_KEY:
        sumber, cari = "Pixabay", kandidat_pixabay
    elif PEXELS_KEY:
        sumber, cari = "Pexels", kandidat_pexels
    else:
        print("  (PIXABAY_API_KEY / PEXELS_API_KEY kosong, b-roll dilewati)")
        return naskah
    print(f"  sumber video latar: {sumber}")
    folder = siapkan_folder(ROOT / "public" / "broll" / slug)

    # 1) kumpulkan kandidat tiap scene beserta cuplikan gambarnya
    tugas = []
    for i, s in enumerate(naskah["scenes"]):
        queries = s.get("broll") or []
        if not queries:
            continue
        try:
            pool: list = []
            for q in queries:
                for k in cari(q, set()):
                    if all(k["id"] != x["id"] for x in pool):
                        pool.append(k)
                if len(pool) >= 12:
                    break
            valid = []
            for k in peringkat(pool, queries, s["durasi"], batas=4):
                if not k["thumb"]:
                    continue
                try:
                    k["_gambar"] = _ambil_gambar(k["thumb"])
                    valid.append(k)
                except Exception:
                    continue
            if valid:
                tugas.append({"i": i, "narasi": s["narasi"], "kands": valid})
                print(f"  scene {i}: {len(valid)} kandidat untuk {queries}")
            else:
                print(f"  scene {i}: tidak ada video untuk {queries}, pakai latar biasa")
            time.sleep(0.5)
        except Exception as e:
            print(f"  scene {i}: pencarian gagal ({e}), lanjut tanpa video latar")

    naskah["kredit_broll"] = []
    if not tugas:
        return naskah

    # 2) satu panggilan Gemini memilih untuk semua scene sekaligus
    pilihan = kurator_batch(topik, tugas)

    # 3) unduh yang terpilih (satu video tidak dipakai dua kali)
    dipakai: set = set()
    for tg in tugas:
        i = tg["i"]
        pilih = pilihan.get(i)
        if not pilih or pilih["id"] in dipakai:
            print(f"  scene {i}: tidak ada footage yang cocok, pakai latar biasa")
            continue
        try:
            unduh(pilih["link"], folder / f"scene_{i}.mp4")
            naskah["scenes"][i]["brollSrc"] = f"broll/{slug}/scene_{i}.mp4"
            dipakai.add(pilih["id"])
            naskah["kredit_broll"].append(
                f"Video by {pilih['pembuat']} on {sumber} ({naskah['scenes'][i]['broll'][0]})"
            )
            print(f"  scene {i}: b-roll terpasang")
        except Exception as e:  # b-roll hanya pemanis, jangan sampai menggagalkan video
            print(f"  scene {i}: unduh gagal ({e}), lanjut tanpa video latar")
    return naskah


# ---------------------------------------------------------------- Ilustrator

def _url_gambar(prompt: str, seed: int, kunci: str):
    q = urllib.parse.quote(prompt, safe="")
    param = f"width=864&height=1536&seed={seed}&model=flux&nologo=true&safe=true&enhance=false"
    if kunci:
        return f"https://gen.pollinations.ai/image/{q}?{param}", {"Authorization": f"Bearer {kunci}", **UA}
    return f"https://image.pollinations.ai/prompt/{q}?{param}", UA


def buat_gambar(prompt: str, path: Path, seed: int) -> bool:
    """Buat satu ilustrasi lewat Pollinations. Mencoba beberapa kali; True bila berhasil."""
    target = []
    if POLLI_KEY:
        target.append(_url_gambar(prompt, seed, POLLI_KEY))
    target.append(_url_gambar(prompt, seed, ""))
    for url, hdr in target:
        for percobaan in range(1, 4):
            try:
                req = urllib.request.Request(url, headers=hdr)
                with urllib.request.urlopen(req, timeout=150) as r:
                    tipe = r.headers.get("Content-Type", "")
                    data = r.read()
                if tipe.startswith("image/") and len(data) > 5000:
                    path.write_bytes(data)
                    return True
                print(f"    bukan gambar ({tipe}, {len(data)} byte)")
            except urllib.error.HTTPError as e:
                print(f"    HTTP {e.code} (percobaan {percobaan})")
                if e.code in (401, 403):
                    break  # kunci/endpoint ditolak: coba endpoint berikutnya
            except Exception as e:
                print(f"    gagal ({e}) percobaan {percobaan}")
            time.sleep(20 * percobaan)
    return False


def agen_ilustrator(naskah: dict, slug: str) -> dict:
    """Agen Ilustrator: membuat gambar kartun bergaya buku cerita untuk tiap scene."""
    folder = siapkan_folder(ROOT / "public" / "gambar" / slug)
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:6], 16) % 100000  # seed sama = gaya lebih konsisten
    jeda = 3 if POLLI_KEY else 16  # tanpa kunci, batasnya sekitar 1 gambar per 15 detik
    dibuat = berhasil = 0
    for i, s in enumerate(naskah["scenes"]):
        if not s.get("gambar") or dibuat >= MAKS_GAMBAR:
            continue
        prompt = GAYA_INFO[naskah["gaya"]]["template"].format(desc=s["gambar"])[:700]
        print(f"  scene {i}: membuat ilustrasi...")
        dibuat += 1
        if buat_gambar(prompt, folder / f"scene_{i}.jpg", seed):
            s["gambarSrc"] = f"gambar/{slug}/scene_{i}.jpg"
            berhasil += 1
        else:
            print(f"  scene {i}: ilustrasi gagal, memakai latar polos")
        time.sleep(jeda)
    print(f"  ilustrasi berhasil: {berhasil} dari {dibuat} (gaya {naskah['gaya']})")
    return naskah


# ---------------------------------------------------------------- utama

def pilih_topik() -> str:
    arg = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if arg:
        return arg
    baris = [b.strip() for b in (ROOT / "topik.txt").read_text(encoding="utf-8").splitlines() if b.strip()]
    if not baris:
        raise SystemExit("topik.txt kosong dan tidak ada topik diberikan.")
    return baris[datetime.date.today().toordinal() % len(baris)]


def pilih(nama_env: str, valid: list, bawaan: str) -> str:
    """Baca pilihan dari env; 'acak' memilih secara acak, nilai asing kembali ke bawaan."""
    nilai = (os.environ.get(nama_env) or bawaan).strip().lower()
    if nilai == "acak":
        return random.choice(valid)
    return nilai if nilai in valid else bawaan


def pilih_durasi() -> int:
    mentah = sys.argv[2].strip() if len(sys.argv) > 2 else (os.environ.get("DURASI") or "75")
    try:
        d = int(float(mentah))
    except ValueError:
        d = 75
    return max(30, min(d, 240))


def main() -> None:
    topik = pilih_topik()
    durasi = pilih_durasi()
    slug = re.sub(r"[^a-z0-9]+", "-", topik.lower()).strip("-")[:40] or "video"
    print(f"Topik: {topik} | target durasi: {durasi} detik")

    paksa = GAYA_ENV if GAYA_ENV in GAYA_VALID else ""
    print("[1/4] Agen Naskah + pemilih gaya...")
    naskah = agen_naskah(topik, durasi, paksa)
    print(f"  gaya terpilih: {naskah['gaya']}" + (" (ditentukan manual)" if paksa else " (dipilih otomatis dari topik)"))
    print("[2/4] Agen Pemeriksa Fakta...")
    naskah = agen_fakta(naskah, topik)
    if paksa:
        naskah["gaya"] = paksa
    catatan = naskah.get("catatan_fakta") or []
    print("[3/4] Agen Suara + Subtitle...")
    naskah = asyncio.run(agen_suara(naskah, slug))
    print("[4/4] Agen Ilustrator (gambar kartun)...")
    naskah = agen_ilustrator(naskah, slug)
    if os.environ.get("BROLL") == "ya":  # opsional: video stok sebagai tambahan (bawaan: mati)
        print("[+] Agen Kurator Footage (b-roll)...")
        naskah = agen_broll(naskah, slug, topik)

    buat_sfx(siapkan_folder(ROOT / "public" / "sfx"))  # efek suara dibuat lewat kode (file buatan sendiri didahulukan)
    naskah["sfx"] = peta_sfx(ROOT / "public")
    info = GAYA_INFO[naskah["gaya"]]
    if naskah["gaya"] == "STYLE_CLAY_3D":
        naskah["latar"] = LATAR_CLAY[int(hashlib.md5(slug.encode()).hexdigest()[:2], 16) % len(LATAR_CLAY)]
    print(f"Tampilan: {naskah['gaya']}")
    for berkas in (info["musik"], "musik.mp3"):  # musik khusus gaya didahulukan
        if (ROOT / "public" / berkas).exists():
            naskah["musikSrc"] = berkas
            print(f"Musik latar: {berkas}")
            break
    else:
        print(f"(Tidak ada musik. Taruh {info['musik']} atau musik.mp3 di folder public/ bila ingin musik latar.)")

    (ROOT / "data").mkdir(exist_ok=True)
    for nama in (f"{slug}.json", "latest.json"):
        (ROOT / "data" / nama).write_text(json.dumps(naskah, ensure_ascii=False, indent=2), encoding="utf-8")

    u = naskah.get("unggah") or {}
    info = (
        f"JUDUL: {u.get('judul', '')}\n\nDESKRIPSI: {u.get('deskripsi', '')}\n\n"
        f"HASHTAG: {' '.join(u.get('hashtag', []))}\n"
    )
    (ROOT / "data" / "info-unggah.txt").write_text(info, encoding="utf-8")
    print("\nBahan unggah (juga ada di data/info-unggah.txt):\n" + info)
    print(f"\nTersimpan: data/{slug}.json (dan data/latest.json)")
    if catatan:
        print("\nCek manual sebelum upload:")
        for c in catatan:
            print(f"  - {c}")
    if naskah.get("kredit_broll"):
        print("\nKredit video latar (opsional dicantumkan di deskripsi):")
        for k in naskah["kredit_broll"]:
            print(f"  - {k}")
    print("\nLanjut render: npm run render")


if __name__ == "__main__":
    main()
