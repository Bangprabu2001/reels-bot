"""Pipeline agen: Naskah -> Pemeriksa Fakta -> Suara+Subtitle -> B-roll -> data/latest.json

Pemakaian:
    pip install -r scripts/requirements.txt
    export GEMINI_API_KEY=...            # wajib
    export PIXABAY_API_KEY=...           # opsional: video latar (b-roll); atau PEXELS_API_KEY
    python3 scripts/pipeline.py "kenapa langit berwarna biru" 90
        (angka terakhir = durasi target dalam detik; bisa juga lewat env DURASI)
    python3 scripts/pipeline.py          # tanpa topik: ambil dari topik.txt
Setelah itu render: npm run render
"""
import asyncio
import datetime
import json
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import edge_tts

from llm import tanya_json

ROOT = Path(__file__).resolve().parent.parent
VOICE = os.environ.get("VOICE", "id-ID-ArdiNeural")  # alternatif: id-ID-GadisNeural
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "").strip()
ALLOWED = {"hook", "bar_chart", "list", "big_number", "compare", "timeline", "outro"}
EKSPRESI = {"senang", "kaget", "mikir"}

SKEMA = """Jenis scene yang boleh dipakai (semuanya boleh punya "ekspresi" dan "broll"):
- {"type":"hook","durasi":3,"narasi":"...","teks":"kalimat pendek; kata penting diapit *bintang*"}
- {"type":"bar_chart","durasi":6,"narasi":"...","judul":"...","satuan":"...","data":[{"label":"...","nilai":0}]}
- {"type":"list","durasi":7,"narasi":"...","judul":"...","poin":[{"ikon":"satu emoji","teks":"..."}]}
- {"type":"big_number","durasi":6,"narasi":"...","judul":"...","angka":0,"satuan":"...","keterangan":"..."}
- {"type":"compare","durasi":8,"narasi":"...","judul":"...","kiri":{"nama":"...","poin":["..."]},"kanan":{"nama":"...","poin":["..."]}}
- {"type":"timeline","durasi":8,"narasi":"...","judul":"...","langkah":[{"label":"...","teks":"..."}]}
- {"type":"outro","durasi":4,"narasi":"...","teks":"ajakan singkat; kata penting diapit *bintang*"}
Field umum: "ekspresi" = "senang" | "kaget" | "mikir"; "broll" = kata kunci bahasa Inggris untuk video stok (atau "")."""


def sys_naskah(durasi: int) -> str:
    kata = int(durasi * 2.4)
    n = max(5, round(durasi / 9))
    return f"""Kamu Agen Naskah untuk video pendek (Reels/Shorts) berbahasa Indonesia: hiburan + edukasi, ritme cepat, santai.
Balas HANYA JSON valid berbentuk {{"scenes":[...]}}.
{SKEMA}
Aturan:
- Target total sekitar {durasi} detik: seluruh narasi sekitar {kata} kata, sekitar {n} scene.
- Struktur: hook (scene pertama) -> konteks singkat -> 3-5 bagian isi yang membahas topik sampai tuntas (jelaskan sebab-akibat, bukan sekadar daftar) -> ringkasan -> outro (scene terakhir).
- Variasikan jenis scene; jangan memakai jenis yang sama lebih dari dua kali berturut-turut. Pakai bar_chart, big_number, atau compare hanya jika ada data nyata.
- Narasi lisan dan natural, maksimal sekitar 40 kata per scene. Jangan menyebut kata "scene".
- Hanya fakta yang kamu yakin akurat; angka boleh dibulatkan; jangan mengarang statistik atau sumber.
- "ekspresi" menyesuaikan nada narasi.
- "broll": 2-3 kata kunci bahasa Inggris untuk video stok yang konkret dan bisa difilmkan (contoh "ocean waves", "city traffic"), atau "" bila sebaiknya tanpa video. Gunakan di sekitar separuh scene.
- Batas: bar_chart maksimal 5 batang, list maksimal 4 poin, compare maksimal 3 poin per sisi, timeline maksimal 4 langkah; teks di layar singkat."""


SYS_FAKTA = f"""Kamu Agen Pemeriksa Fakta. Kamu menerima naskah video JSON.
Periksa setiap klaim dan angka. Perbaiki yang salah atau meragukan, ganti dengan versi yang lebih aman (misalnya pembulatan atau kata 'sekitar').
Pertahankan struktur, urutan scene, dan semua field (termasuk "ekspresi" dan "broll") kecuali yang perlu diperbaiki.
Balas HANYA JSON valid dengan bentuk {{"scenes":[...]}}, ditambah field
"catatan_fakta": daftar string singkat tentang hal yang perlu dicek manusia (kosongkan jika tidak ada).
{SKEMA}"""


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
        elif t == "big_number":
            try:
                s["angka"] = float(s["angka"])
            except (TypeError, ValueError, KeyError):
                raise SystemExit("Angka pada scene big_number tidak valid.")
            if s["angka"].is_integer():
                s["angka"] = int(s["angka"])
        if s.get("ekspresi") not in EKSPRESI:
            s["ekspresi"] = "senang"
        s["broll"] = str(s.get("broll") or "").strip()
    if scenes[-1].get("type") != "outro":
        scenes.append(
            {
                "type": "outro",
                "durasi": 4,
                "ekspresi": "senang",
                "broll": "",
                "narasi": "Ikuti untuk fakta seru lainnya!",
                "teks": "Ikuti untuk fakta *seru* lainnya!",
            }
        )
    return n


def agen_naskah(topik: str, durasi: int) -> dict:
    return validasi(tanya_json(sys_naskah(durasi), f"Topik: {topik}"))


def agen_fakta(naskah: dict, topik: str) -> dict:
    hasil = tanya_json(SYS_FAKTA, f"Topik: {topik}\n\nNaskah:\n{json.dumps(naskah, ensure_ascii=False)}")
    return validasi(hasil)


async def sintesis(teks: str, path: Path) -> list:
    try:
        comm = edge_tts.Communicate(teks, VOICE, boundary="WordBoundary")
    except TypeError:  # edge-tts versi lama: default-nya sudah WordBoundary
        comm = edge_tts.Communicate(teks, VOICE)
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


async def agen_suara(naskah: dict, slug: str) -> dict:
    folder = ROOT / "public" / "audio" / slug
    folder.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(naskah["scenes"]):
        file = folder / f"scene_{i}.mp3"
        kata = await sintesis(s["narasi"], file)
        s["audioSrc"] = f"audio/{slug}/scene_{i}.mp3"
        s["kata"] = kata
        # durasi scene = akhir kata terakhir + jeda napas
        s["durasi"] = round((kata[-1]["selesai"] + 0.6) if kata else max(2.5, len(s["narasi"]) / 14), 2)
        print(f"  scene {i} ({s['type']}): {s['durasi']} detik")
    total = sum(s["durasi"] for s in naskah["scenes"])
    print(f"  total video: {round(total)} detik")
    return naskah


def _json(url: str, headers=None) -> dict:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "reels-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _pexels(url: str) -> dict:
    return _json(url, {"Authorization": PEXELS_KEY, "User-Agent": "reels-bot"})


def cari_broll(query: str, min_detik: float, dipakai: set):
    """Cari video stok di Pexels; utamakan yang portrait dan cukup panjang."""
    for orientasi in ("portrait", None):
        param = {"query": query, "per_page": 12}
        if orientasi:
            param["orientation"] = orientasi
        data = _pexels("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(param))
        videos = [v for v in data.get("videos", []) if v.get("id") not in dipakai]
        videos.sort(key=lambda v: v.get("duration", 0) < min_detik)  # klip cukup panjang lebih dulu
        for v in videos:
            files = [
                f
                for f in v.get("video_files", [])
                if f.get("file_type") == "video/mp4" and (f.get("width") or 0) >= 540
            ]
            if not files:
                continue
            f = min(files, key=lambda f: abs(f["width"] - 720))  # ukuran sedang, hemat unduhan
            return f["link"], v["id"], (v.get("user") or {}).get("name", "?")
    return None


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


def _portrait_pixabay(hit: dict) -> bool:
    return any(
        (v or {}).get("height", 0) > (v or {}).get("width", 0)
        for v in (hit.get("videos") or {}).values()
    )


def cari_broll_pixabay(query: str, min_detik: float, dipakai: set):
    """Cari video stok di Pixabay. Kebanyakan landscape; di layar dipotong bagian tengahnya."""
    kandidat: list = []
    for tinggi_min in (1280, 0):  # coba cari yang portrait dulu
        param = {
            "key": PIXABAY_KEY,
            "q": query[:100],
            "video_type": "all",
            "per_page": 20,
            "safesearch": "true",
        }
        if tinggi_min:
            param["min_height"] = tinggi_min
        data = _json("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(param))
        kandidat = [h for h in data.get("hits", []) if h.get("id") not in dipakai]
        if tinggi_min:
            kandidat = [h for h in kandidat if _portrait_pixabay(h)]
        if kandidat:
            break
    kandidat.sort(key=lambda h: h.get("duration", 0) < min_detik)  # klip cukup panjang lebih dulu
    for h in kandidat:
        v = _varian_pixabay(h)
        if v:
            return v["url"], h["id"], h.get("user", "?")
    return None


def unduh(link: str, path: Path) -> None:
    req = urllib.request.Request(link, headers={"User-Agent": "reels-bot"})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        shutil.copyfileobj(r, f)


def agen_broll(naskah: dict, slug: str) -> dict:
    if PIXABAY_KEY:
        sumber, cari = "Pixabay", cari_broll_pixabay
    elif PEXELS_KEY:
        sumber, cari = "Pexels", cari_broll
    else:
        print("  (PIXABAY_API_KEY / PEXELS_API_KEY kosong, b-roll dilewati)")
        return naskah
    print(f"  sumber video latar: {sumber}")
    folder = ROOT / "public" / "broll" / slug
    folder.mkdir(parents=True, exist_ok=True)
    dipakai: set = set()
    kredit = []
    for i, s in enumerate(naskah["scenes"]):
        q = s.get("broll")
        if not q:
            continue
        try:
            hasil = cari(q, s["durasi"], dipakai)
            if not hasil:
                print(f"  scene {i}: tidak ada video untuk '{q}', dilewati")
                continue
            link, vid, pembuat = hasil
            unduh(link, folder / f"scene_{i}.mp4")
            s["brollSrc"] = f"broll/{slug}/scene_{i}.mp4"
            dipakai.add(vid)
            kredit.append(f"Video by {pembuat} on {sumber} ({q})")
            print(f"  scene {i}: b-roll '{q}' terpasang")
        except Exception as e:  # b-roll hanya pemanis, jangan sampai menggagalkan video
            print(f"  scene {i}: b-roll gagal ({e}), lanjut tanpa video latar")
    naskah["kredit_broll"] = kredit
    return naskah


def pilih_topik() -> str:
    arg = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if arg:
        return arg
    baris = [b.strip() for b in (ROOT / "topik.txt").read_text(encoding="utf-8").splitlines() if b.strip()]
    if not baris:
        raise SystemExit("topik.txt kosong dan tidak ada topik diberikan.")
    return baris[datetime.date.today().toordinal() % len(baris)]


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

    print("[1/4] Agen Naskah...")
    naskah = agen_naskah(topik, durasi)
    print("[2/4] Agen Pemeriksa Fakta...")
    naskah = agen_fakta(naskah, topik)
    catatan = naskah.get("catatan_fakta") or []
    print("[3/4] Agen Suara + Subtitle...")
    naskah = asyncio.run(agen_suara(naskah, slug))
    print("[4/4] Agen B-roll...")
    naskah = agen_broll(naskah, slug)

    if (ROOT / "public" / "musik.mp3").exists():
        naskah["musikSrc"] = "musik.mp3"

    (ROOT / "data").mkdir(exist_ok=True)
    for nama in (f"{slug}.json", "latest.json"):
        (ROOT / "data" / nama).write_text(json.dumps(naskah, ensure_ascii=False, indent=2), encoding="utf-8")

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
