"""Pipeline agen: Naskah -> Pemeriksa Fakta -> Suara+Subtitle -> data/latest.json

Pemakaian:
    pip install -r scripts/requirements.txt
    export GEMINI_API_KEY=...
    python3 scripts/pipeline.py "kenapa langit berwarna biru"
    python3 scripts/pipeline.py            # tanpa topik: ambil dari topik.txt
Setelah itu render: npm run render
"""
import asyncio
import datetime
import json
import os
import re
import sys
from pathlib import Path

import edge_tts

from llm import tanya_json

ROOT = Path(__file__).resolve().parent.parent
VOICE = os.environ.get("VOICE", "id-ID-ArdiNeural")  # alternatif: id-ID-GadisNeural
ALLOWED = {"hook", "bar_chart", "list"}

SKEMA = """Jenis scene yang boleh dipakai:
- {"type":"hook","durasi":3,"narasi":"...","teks":"kalimat pendek; kata penting diapit *bintang*"}
- {"type":"bar_chart","durasi":6,"narasi":"...","judul":"...","satuan":"...","data":[{"label":"...","nilai":0}]}
- {"type":"list","durasi":7,"narasi":"...","judul":"...","poin":[{"ikon":"satu emoji","teks":"..."}]}"""

SYS_NASKAH = f"""Kamu Agen Naskah untuk video pendek (Reels/Shorts) berbahasa Indonesia: hiburan + edukasi, ritme cepat, santai.
Balas HANYA JSON valid berbentuk {{"scenes":[...]}}.
{SKEMA}
Aturan:
- Total 30-45 detik, scene pertama harus hook, 3-5 scene.
- Narasi lisan dan natural, maksimal sekitar 35 kata per scene.
- Hanya fakta yang kamu yakin akurat; angka boleh dibulatkan.
- Bar chart maksimal 5 batang, list maksimal 4 poin, teks di layar singkat."""

SYS_FAKTA = f"""Kamu Agen Pemeriksa Fakta. Kamu menerima naskah video JSON.
Periksa setiap klaim dan angka. Perbaiki yang salah atau meragukan, ganti dengan versi yang lebih aman (misalnya pembulatan atau kata 'sekitar').
Balas HANYA JSON valid dengan bentuk scene yang sama persis ({{"scenes":[...]}}), ditambah field
"catatan_fakta": daftar string singkat tentang hal yang perlu dicek manusia (kosongkan jika tidak ada).
{SKEMA}"""


def validasi(n: dict) -> dict:
    scenes = n.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise SystemExit("Naskah kosong atau bentuknya salah.")
    if scenes[0].get("type") != "hook":
        raise SystemExit("Scene pertama harus hook.")
    for s in scenes:
        if s.get("type") not in ALLOWED:
            raise SystemExit(f"Tipe scene tidak dikenal: {s.get('type')}")
        if s["type"] == "bar_chart":
            s["data"] = s["data"][:5]
        if s["type"] == "list":
            s["poin"] = s["poin"][:4]
    return n


def agen_naskah(topik: str) -> dict:
    return validasi(tanya_json(SYS_NASKAH, f"Topik: {topik}"))


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
    return naskah


def pilih_topik() -> str:
    arg = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if arg:
        return arg
    baris = [b.strip() for b in (ROOT / "topik.txt").read_text(encoding="utf-8").splitlines() if b.strip()]
    if not baris:
        raise SystemExit("topik.txt kosong dan tidak ada topik diberikan.")
    return baris[datetime.date.today().toordinal() % len(baris)]


def main() -> None:
    topik = pilih_topik()
    slug = re.sub(r"[^a-z0-9]+", "-", topik.lower()).strip("-")[:40] or "video"
    print(f"Topik: {topik}")

    print("[1/3] Agen Naskah...")
    naskah = agen_naskah(topik)
    print("[2/3] Agen Pemeriksa Fakta...")
    naskah = agen_fakta(naskah, topik)
    catatan = naskah.get("catatan_fakta") or []
    print("[3/3] Agen Suara + Subtitle...")
    naskah = asyncio.run(agen_suara(naskah, slug))

    (ROOT / "data").mkdir(exist_ok=True)
    for nama in (f"{slug}.json", "latest.json"):
        (ROOT / "data" / nama).write_text(json.dumps(naskah, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nTersimpan: data/{slug}.json (dan data/latest.json)")
    if catatan:
        print("\nCek manual sebelum upload:")
        for c in catatan:
            print(f"  - {c}")
    print("\nLanjut render: npm run render")


if __name__ == "__main__":
    main()
