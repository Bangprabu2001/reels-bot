"""TAHAP 1 - TOPIC HUNTER: cari topik fresh dengan sudut pandang baru."""
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

from .common import gemini_json, load_db, log, mirip, sudah_ada
from .s2_router import rules_block

UA = {"User-Agent": "Mozilla/5.0 (pabrik-konten)"}
TRENDS_URLS = [
    "https://trends.google.com/trending/rss?geo=ID",
    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=ID",
]
GENERIK = ["cara kaya", "tips sukses", "rahasia sukses", "cara cepat kaya", "motivasi sukses", "tips bisnis"]


def _ln(tag):
    return tag.split("}")[-1]


def ambil_trends():
    for url in TRENDS_URLS:
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            hasil = []
            for item in root.iter("item"):
                judul, berita = "", []
                for ch in item:
                    if _ln(ch.tag) == "title":
                        judul = (ch.text or "").strip()
                    if _ln(ch.tag) == "news_item":
                        for x in ch:
                            if _ln(x.tag) == "news_item_title":
                                berita.append((x.text or "").strip())
                if judul:
                    hasil.append(judul + (" | " + " / ".join(berita[:2]) if berita else ""))
            if hasil:
                return hasil[:40]
        except Exception as e:
            log(f"[topic] trends gagal {url}: {e}")
    return []


def ambil_berita(kata_cari):
    hasil = []
    for q in kata_cari[:5]:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": f"{q} when:7d", "hl": "id", "gl": "ID", "ceid": "ID:id"})
        try:
            r = requests.get(url, headers=UA, timeout=30)
            root = ET.fromstring(r.content)
            for item in list(root.iter("item"))[:8]:
                t = item.findtext("title")
                if t:
                    hasil.append(t.strip())
        except Exception as e:
            log(f"[topic] berita gagal '{q}': {e}")
    return hasil[:40]


def hitung_video_serupa(kata_cari, judul):
    """Cek YouTube 30 hari terakhir (butuh YOUTUBE_API_KEY, opsional).
    Mengembalikan jumlah video yang judulnya mirip, atau None kalau tidak bisa dicek."""
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        return None
    try:
        sejak = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet", "q": kata_cari, "type": "video", "maxResults": 25,
            "publishedAfter": sejak, "regionCode": "ID", "relevanceLanguage": "id", "key": key}, timeout=30)
        items = r.json().get("items", [])
        return sum(1 for i in items if mirip(i["snippet"]["title"], judul) >= 0.55)
    except Exception as e:
        log(f"[topic] cek YouTube gagal: {e}")
        return None


def cari_topik(mode, percobaan=3):
    """Mengembalikan dict topik terpilih. Melempar RuntimeError kalau semua ide ditolak."""
    db = load_db()
    trends = ambil_trends()
    berita = ambil_berita(mode["kata_cari_berita"])
    log(f"[topic] bahan mentah: {len(trends)} tren, {len(berita)} berita")
    ditolak_log = []
    sudah = [x["judul"] for x in db["disetujui"][-60:]] + [x["judul"] for x in db["dibuang"][-30:]] \
        + [x["judul"] for x in db["dibuat_ulang"][-30:]]

    for ke in range(1, percobaan + 1):
        prompt = f"""Kamu TOPIC HUNTER untuk pabrik konten video pendek Indonesia.

{rules_block(mode, dengan_visual=False)}

BAHAN MENTAH (tren Google Indonesia): {trends or 'kosong'}
BAHAN MENTAH (berita 7 hari terakhir): {berita or 'kosong'}
TOPIK YANG SUDAH PERNAH DIBUAT/DITOLAK, JANGAN ULANGI: {sudah + ditolak_log or 'belum ada'}

Buat 8 ide topik. Aturan keras:
1. Dilarang generik seperti "Cara Kaya" atau "Tips Sukses".
2. Setiap ide WAJIB punya SUDUT PANDANG BARU, berbentuk perbandingan/pertanyaan tajam. Contoh gaya yang diinginkan: "{mode['contoh_judul']}".
3. Topik harus cocok untuk MODE {mode['id']} dan bisa dibuktikan dengan data asli yang bisa dicari di internet.
4. Boleh terinspirasi bahan mentah, tapi jangan menyalin judul berita.

Jawab HANYA JSON array berisi 8 objek:
{{"judul": "...", "sudut_baru": "apa sudut pandang barunya", "kenapa_belum_dibahas": "...", "kata_cari": "2-5 kata untuk cek video serupa", "generik": false, "skor_baru": 1-10}}"""
        ide = gemini_json(prompt, temperature=1.0)
        if isinstance(ide, dict):
            ide = ide.get("ide") or list(ide.values())[0]
        ide = sorted(ide, key=lambda x: -float(x.get("skor_baru", 0) or 0))

        for i in ide:
            judul = (i.get("judul") or "").strip()
            if not judul:
                continue
            low = judul.lower()
            if i.get("generik") or any(g in low for g in GENERIK) or len(judul.split()) < 5:
                ditolak_log.append(judul)
                log(f"[topic] TOLAK generik: {judul}")
                continue
            if not (i.get("sudut_baru") or "").strip():
                ditolak_log.append(judul)
                continue
            ada = sudah_ada(judul, db)
            if ada:
                ditolak_log.append(judul)
                log(f"[topic] TOLAK sudah ada di database ({ada}): {judul}")
                continue
            n = hitung_video_serupa(i.get("kata_cari", judul), judul)
            if n is not None and n > 5:
                ditolak_log.append(judul)
                log(f"[topic] TOLAK pasaran ({n} video serupa/30 hari): {judul}")
                continue
            i["judul"] = judul
            i["cek_pasaran"] = (f"{n} video serupa dalam 30 hari" if n is not None
                                else "tidak dicek (YOUTUBE_API_KEY belum diisi)")
            log(f"[topic] TERPILIH: {judul}")
            return i
        log(f"[topic] percobaan {ke}: semua ide ditolak, buat ide baru")
    raise RuntimeError("Semua ide topik ditolak filter. Coba jalankan lagi.")
