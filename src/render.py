"""Produksi video: gambar (Pollinations), suara (edge-tts), lalu render frame per frame.
Overlay (split screen, timeline, tabel, grafik, dalil, letterbox, subtitle) digambar kode,
jadi aturan editing tiap mode ditegakkan oleh program, bukan hanya oleh AI."""
import asyncio
import glob
import io
import math
import os
import re
import subprocess
import time
import wave
from pathlib import Path
from urllib.parse import quote

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, features

from .common import ROOT, log

W, H, FPS, SR = 720, 1280, 24, 24000
OFFLINE = os.environ.get("OFFLINE", "") == "1"
RAQM = features.check("raqm")  # kalau ada, Pillow menyambung huruf Arab sendiri

# ------------------------------------------------------------------ font
_FC = {}


def _cands(kind):
    dj = "/usr/share/fonts/truetype/dejavu/"
    lib = "/usr/share/fonts/truetype/liberation/"
    if kind == "arab":
        c = ["/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
             "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
             "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"]
        c += glob.glob("/usr/share/fonts/**/*Arabic*.ttf", recursive=True)
        return c + [dj + "DejaVuSans-Bold.ttf"]
    if kind == "bold":
        return [dj + "DejaVuSans-Bold.ttf", lib + "LiberationSans-Bold.ttf"]
    return [dj + "DejaVuSans.ttf", lib + "LiberationSans-Regular.ttf"]


def F(kind, size):
    k = (kind, size)
    if k not in _FC:
        font = None
        for p in _cands(kind):
            if os.path.exists(p):
                try:
                    if kind == "arab":
                        eng = ImageFont.Layout.RAQM if RAQM else ImageFont.Layout.BASIC
                        font = ImageFont.truetype(p, size, layout_engine=eng)
                    else:
                        font = ImageFont.truetype(p, size)
                    break
                except Exception:
                    continue
        _FC[k] = font or ImageFont.load_default()
    return _FC[k]


def ar(teks):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(teks))
    except Exception:
        return teks


def lebar_ar(d, s, font):
    if RAQM:
        return d.textlength(s, font=font, direction="rtl", language="ar")
    return d.textlength(ar(s), font=font)


def tulis_ar(d, xy, s, font, fill):
    if RAQM:
        d.text(xy, s, font=font, fill=fill, anchor="mt", direction="rtl", language="ar")
    else:
        d.text(xy, ar(s), font=font, fill=fill, anchor="mt")


def baris_arab(d, teks, font, max_w):
    kata, baris, cur = teks.split(), [], []
    for w in kata:
        if cur and lebar_ar(d, " ".join(cur + [w]), font) > max_w:
            baris.append(" ".join(cur))
            cur = []
        cur.append(w)
    if cur:
        baris.append(" ".join(cur))
    return baris


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


# ------------------------------------------------------------------ gambar
def _placeholder(out, i, mode_id, label=""):
    warna = {"1": [(70, 50, 30), (200, 150, 80)], "2": [(120, 100, 70), (245, 238, 221)],
             "3": [(10, 40, 90), (60, 120, 190)]}[mode_id]
    t = np.linspace(0, 1, H)[:, None, None]
    a, b = np.array(warna[0])[None, None, :], np.array(warna[1])[None, None, :]
    arr = (a + (b - a) * t * (0.6 + 0.1 * i)).astype(np.uint8)
    arr = np.repeat(arr, W, axis=1)
    im = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(im)
    d.text((W // 2, H // 2), f"GAMBAR {i + 1}\n{label}", font=F("bold", 44), fill=(255, 255, 255),
           anchor="mm", align="center", stroke_width=3, stroke_fill=(0, 0, 0))
    im.save(out, quality=90)


def _pollinations(prompt, seed, out):
    if " Style: " in prompt or ". Style: " in prompt:
        raw, _, gaya = prompt.partition(". Style: ")
        prompt = raw[:650] + ". Style: " + gaya
    url = f"https://image.pollinations.ai/prompt/{quote(prompt[:1500])}?width={W}&height={H}&seed={seed}&nologo=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    tok = os.environ.get("POLLINATIONS_TOKEN", "").strip()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    for k in range(4):
        try:
            r = requests.get(url, headers=headers, timeout=240)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                Image.open(io.BytesIO(r.content)).convert("RGB").save(out, quality=92)
                return True
            log(f"[gambar] status {r.status_code}, coba lagi")
            time.sleep(22 if r.status_code == 429 else 8)
        except Exception as e:
            log(f"[gambar] error {e}")
            time.sleep(8)
    return False


def bikin_gambar(prompts, folder, mode, seed):
    paths, berhasil = [], 0
    for i, p in enumerate(prompts):
        out = Path(folder) / f"gambar_{i + 1}.jpg"
        ok = False
        if not OFFLINE:
            ok = _pollinations(p, seed, out)
            if i < len(prompts) - 1:
                time.sleep(16)  # batas pemakaian gratis tanpa akun: 1 gambar per ~15 detik
        if ok:
            berhasil += 1
        else:
            _placeholder(out, i, mode["id"], "(gagal dibuat)" if not OFFLINE else "(uji tampilan)")
        paths.append(out)
    return paths, berhasil


# ------------------------------------------------------------------ suara
def pecah_kalimat(teks):
    teks = re.sub(r"\s+", " ", str(teks).strip())
    out = []
    for b in re.split(r"(?<=[.!?…])\s+", teks):
        if len(b.split()) > 22:
            out += [x.strip() for x in re.split(r"(?<=,)\s+", b) if x.strip()]
        elif b:
            out.append(b)
    return out


async def _edge(teks, out, voice, rate, pitch):
    import edge_tts
    await edge_tts.Communicate(teks, voice, rate=rate, pitch=pitch).save(str(out))


def _tts_satu(teks, mp3, mode):
    v = mode["voiceover"]
    for _ in range(3):
        try:
            asyncio.run(_edge(teks, mp3, v["tts_voice"], v["tts_rate"], v["tts_pitch"]))
            if Path(mp3).exists() and Path(mp3).stat().st_size > 500:
                return True
        except Exception as e:
            log(f"[suara] error {e}")
            time.sleep(2)
    return False


def _mp3_ke_array(mp3):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ar", str(SR), "-ac", "1",
                        "-f", "s16le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.int16) if r.returncode == 0 else None


def bikin_suara(cerita, mode, folder):
    """Satu kalimat = satu klip suara, jadi waktu subtitle akurat. Mengembalikan (wav, batas_babak, kalimat, total, suara_asli)."""
    jeda = mode["voiceover"]["jeda"]
    arr, t, batas, kalimat, asli, total_k = [np.zeros(int(SR * 0.3), np.int16)], 0.3, [], [], 0, 0
    for bi, b in enumerate(cerita["babak"]):
        mulai = 0.0 if bi == 0 else t
        for j, k in enumerate(pecah_kalimat(b.get("voiceover", ""))):
            mp3 = Path(folder) / f"vo_{bi}_{j}.mp3"
            a = None
            total_k += 1
            if not OFFLINE and _tts_satu(k, mp3, mode):
                a = _mp3_ke_array(mp3)
                if a is not None and len(a) > 0:
                    asli += 1
            if a is None or len(a) == 0:
                dur = max(1.2, len(k.split()) / mode["voiceover"]["kata_per_detik"])
                a = np.zeros(int(SR * dur), np.int16)
            d = len(a) / SR
            kalimat.append((t, t + d, k, bi))
            arr += [a, np.zeros(int(SR * jeda), np.int16)]
            t += d + jeda
        pad = 0.5 if bi < 3 else 1.3
        arr.append(np.zeros(int(SR * pad), np.int16))
        t += pad
        batas.append((mulai, t))
    wav = Path(folder) / "suara.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.concatenate(arr).tobytes())
    return wav, batas, kalimat, t, (asli, total_k)


# ------------------------------------------------------------------ bantu gambar teks
def tata_kata(d, kata, font, max_w):
    sp = d.textlength(" ", font=font)
    baris, cur, cw = [], [], 0.0
    for i, w in enumerate(kata):
        ww = d.textlength(w, font=font)
        if cur and cw + sp + ww > max_w:
            baris.append(cur)
            cur, cw = [], 0.0
        cw += (sp if cur else 0) + ww
        cur.append(i)
    if cur:
        baris.append(cur)
    return baris, sp


def blok(d, cx, y, teks, font, max_w, fill, stroke=None, sw=0, lh=None, anchor_top=True):
    """Teks rata tengah berbaris-baris. Mengembalikan tinggi total."""
    kata = str(teks).split()
    baris, sp = tata_kata(d, kata, font, max_w)
    lh = lh or int(getattr(font, "size", 24) * 1.3)
    for li, idxs in enumerate(baris):
        s = " ".join(kata[i] for i in idxs)
        d.text((cx, y + li * lh), s, font=font, fill=fill, anchor="mt",
               stroke_width=sw, stroke_fill=stroke or (0, 0, 0, 255))
    return len(baris) * lh


def blok_warna(d, cx, y, teks, font, max_w, sorot, warna_sorot, fill, sw, stroke, lh=None, kapital=True):
    kata = str(teks).split()
    norm = lambda w: re.sub(r"[^\w]", "", w.lower())
    kunci = set()
    for s in sorot or []:
        for w in str(s).split():
            kunci.add(norm(w))
    baris, sp = tata_kata(d, kata, font, max_w)
    lh = lh or int(getattr(font, "size", 24) * 1.35)
    n = 0
    for li, idxs in enumerate(baris):
        ws = [(kata[i].upper() if (kapital and norm(kata[i]) in kunci) else kata[i]) for i in idxs]
        tw = sum(d.textlength(w, font=font) for w in ws) + sp * (len(ws) - 1)
        x = cx - tw / 2
        for i, w in zip(idxs, ws):
            ww = d.textlength(w, font=font)
            warna = fill
            if norm(kata[i]) in kunci:
                warna = warna_sorot[n % len(warna_sorot)]
                n += 1
            d.text((x, y + li * lh), w, font=font, fill=warna, anchor="lt", stroke_width=sw, stroke_fill=stroke)
            x += ww + sp
    return len(baris) * lh


def sorot_latar(d, cx, y, teks, font, max_w, kunci, hl, fill, lh=None):
    kata = str(teks).split()
    norm = lambda w: re.sub(r"[^\w]", "", w.lower())
    tandai = [False] * len(kata)
    nk = [norm(w) for w in kata]
    for frasa in kunci or []:
        tk = [norm(w) for w in str(frasa).split() if norm(w)]
        n = len(tk)
        for i in range(len(kata) - n + 1):
            if tk and nk[i:i + n] == tk:
                for j in range(i, i + n):
                    tandai[j] = True
    baris, sp = tata_kata(d, kata, font, max_w)
    lh = lh or int(getattr(font, "size", 24) * 1.45)
    for li, idxs in enumerate(baris):
        tw = sum(d.textlength(kata[i], font=font) for i in idxs) + sp * (len(idxs) - 1)
        x, yy = cx - tw / 2, y + li * lh
        for i in idxs:
            ww = d.textlength(kata[i], font=font)
            if tandai[i]:
                d.rectangle((x - 4, yy - 2, x + ww + 4, yy + lh - 8), fill=hl)
            d.text((x, yy), kata[i], font=font, fill=fill, anchor="lt")
            x += ww + sp
    return len(baris) * lh


def cover(img, w, h, zoom=1.0):
    iw, ih = img.size
    s = max(w / iw, h / ih) * zoom
    nw, nh = int(iw * s) + 1, int(ih * s) + 1
    r = img.resize((nw, nh), Image.BILINEAR)
    l, t = (nw - w) // 2, (nh - h) // 2
    return r.crop((l, t, l + w, t + h))


def format_ribuan(n):
    return f"{int(n):,}".replace(",", ".")


def animasi_angka(teks, prog):
    m = re.search(r"\d[\d.]*", teks)
    if not m:
        return teks
    if re.match(r",\d", teks[m.end():]):
        return teks
    try:
        nilai = int(m.group().rstrip(".").replace(".", ""))
    except ValueError:
        return teks
    if nilai < 10:
        return teks
    return teks[:m.start()] + format_ribuan(nilai * ease(prog)) + teks[m.end():]


WARNA = {"merah": (235, 45, 45), "hijau": (40, 205, 90), "putih": (255, 255, 255)}
KREM, COKLAT, EMAS, ZAITUN = (245, 238, 221), (92, 64, 38), (201, 162, 39), (110, 120, 60)


# ------------------------------------------------------------------ perender
class Perender:
    def __init__(self, mode, cerita, gambar, batas, kalimat, total):
        self.m = mode["id"]
        self.c = cerita
        self.b = cerita["babak"]
        self.batas, self.kal, self.T = batas, kalimat, total
        self.img = [Image.open(p).convert("RGB") for p in gambar]
        rng = np.random.default_rng(7)
        noise = rng.integers(-6, 7, (H, W, 1))
        arr = np.clip(np.array(KREM, dtype=np.int16)[None, None, :] + noise, 0, 255).astype(np.uint8)
        self.kertas = Image.fromarray(arr, "RGB")
        self.lapor = set()

    # --- bantu
    def dimana(self, t):
        bi = len(self.batas) - 1
        for i, (a, b) in enumerate(self.batas):
            if a <= t < b:
                bi = i
                break
        a, b = self.batas[bi]
        return bi, clamp((t - a) / max(0.01, b - a)), t - a, t / self.T

    def kalimat_kini(self, t):
        for (a, b, k, bi) in self.kal:
            if a <= t < b + 0.12:
                return k
        return None

    def aman(self, nama, fn, *a):
        try:
            fn(*a)
        except Exception as e:
            if nama not in self.lapor:
                self.lapor.add(nama)
                log(f"[render] elemen '{nama}' dilewati: {e}")

    # --- frame
    def frame(self, t):
        bi, p, lokal, pg = self.dimana(t)
        base = {"1": self.base1, "2": self.base2, "3": self.base3}[self.m](bi, p, lokal, pg, t)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        {"1": self.over1, "2": self.over2, "3": self.over3}[self.m](d, ov, bi, p, lokal, pg, t)
        out = Image.alpha_composite(base.convert("RGBA"), ov)
        return out.convert("RGB")

    # ============================= MODE 1
    def base1(self, bi, p, lokal, pg, t):
        if bi in (1, 2):
            zoom = 1 + 0.10 * p
            kiri = cover(self.img[1], W // 2, H, zoom)
            kanan = cover(self.img[2], W // 2, H, zoom)
            umur = clamp((pg - 0.13) / 0.7)
            kiri = ImageEnhance.Color(kiri).enhance(1 - 0.55 * umur)
            kiri = ImageEnhance.Brightness(kiri).enhance(1 - 0.22 * umur)
            kanan = ImageEnhance.Brightness(kanan).enhance(1 + 0.06 * umur)
            c = Image.new("RGB", (W, H))
            c.paste(kiri, (0, 0))
            c.paste(kanan, (W // 2, 0))
            ImageDraw.Draw(c).rectangle((W // 2 - 2, 0, W // 2 + 2, H), fill=(255, 255, 255))
            return c
        idx = 0 if bi == 0 else 3
        return cover(self.img[idx], W, H, 1.0 + (0.02 * p if bi == 0 else 0))

    def over1(self, d, ov, bi, p, lokal, pg, t):
        self.aman("timeline", self.timeline, d, bi, p)
        self.aman("judul", self.judul_layar, d, bi, lokal)
        self.aman("angka", self.angka1, d, bi, lokal)
        k = self.kalimat_kini(t)
        if k:
            blok(d, W // 2, H - 250, k, F("bold", 40), 640, (255, 255, 255, 255), (0, 0, 0, 255), 5, lh=50)

    def timeline(self, d, bi, p):
        x0, x1, y = 80, W - 80, 108
        xs = [x0 + i * (x1 - x0) / 4 for i in range(5)]
        label = ["TAHUN 0", "TAHUN 1", "TAHUN 3", "TAHUN 5", "TAHUN 10"]
        d.rounded_rectangle((20, 40, W - 20, 170), 24, fill=(0, 0, 0, 150))
        e = ease(p)
        pos = [(0, 0), (0, 2), (2, 3), (3, 4)][bi]
        px = xs[pos[0]] + (xs[pos[1]] - xs[pos[0]]) * e
        d.line((x0, y, x1, y), fill=(255, 255, 255, 170), width=6)
        d.line((x0, y, px, y), fill=(255, 205, 60, 255), width=8)
        for i, x in enumerate(xs):
            aktif = x <= px + 1
            d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(255, 205, 60, 255) if aktif else (255, 255, 255, 220),
                      outline=(0, 0, 0, 255), width=3)
            d.text((x, y + 34), label[i], font=F("bold", 18), fill=(255, 255, 255, 255), anchor="mm",
                   stroke_width=2, stroke_fill=(0, 0, 0, 255))
        d.polygon([(px, y - 16), (px - 14, y - 40), (px + 14, y - 40)], fill=(255, 60, 60, 255),
                  outline=(0, 0, 0, 255))

    def judul_layar(self, d, bi, lokal):
        teks = (self.b[bi].get("judul_layar") or "").strip()
        if not teks or lokal > 2.6:
            return
        a = int(255 * ease(lokal / 0.4) * (1 - ease((lokal - 2.1) / 0.5)))
        if self.m == "2":
            font = F("bold", 46)
            tw = clamp(d.textlength(teks, font=font) + 70, 200, 660)
            d.rounded_rectangle((W / 2 - tw / 2, 520, W / 2 + tw / 2, 640), 18,
                                fill=KREM + (int(a * 0.9),), outline=EMAS + (a,), width=6)
            blok(d, W // 2, 545, teks, font, 600, COKLAT + (a,), None, 0, lh=56)
        else:
            blok(d, W // 2, 520, teks, F("bold", 54), 640, (255, 255, 255, a), (0, 0, 0, a), 6, lh=66)

    def angka1(self, d, bi, lokal):
        for idx, it in enumerate(self.b[bi].get("angka_melayang") or []):
            mulai = 0.8 + idx * 1.7
            if lokal < mulai:
                continue
            q = lokal - mulai
            a = int(255 * ease(q / 0.4))
            sisi = it.get("sisi", "tengah")
            cx = {"kiri": W * 0.25, "kanan": W * 0.75}.get(sisi, W / 2)
            mw = 330 if sisi in ("kiri", "kanan") and bi in (1, 2) else 620
            y = 330 + idx * 150 - (1 - ease(q / 0.6)) * 40 + math.sin(lokal * 2 + idx) * 7
            teks = animasi_angka(str(it.get("teks", "")), q / 1.4)
            w = WARNA.get(it.get("warna", "putih"), WARNA["putih"])
            blok(d, cx, y, teks, F("bold", 40), mw, w + (a,), (0, 0, 0, a), 6, lh=48)

    # ============================= MODE 2
    def base2(self, bi, p, lokal, pg, t):
        zoom = 1 + 0.03 * p
        cur = cover(self.img[bi], W, H, zoom)
        if bi > 0 and lokal < 1.8:
            prev = cover(self.img[bi - 1], W, H, 1.03)
            e = ease(lokal / 1.6)
            y = int((1 - e) * H * 0.55)
            c = prev.copy()
            c.paste(cur, (0, y))
            dd = ImageDraw.Draw(c, "RGBA")
            dd.rectangle((0, max(0, y - 16), W, y), fill=(0, 0, 0, 60))
            dd.rectangle((W // 2 - 2, y, W // 2 + 2, H), fill=(60, 40, 20, int(90 * (1 - e))))
            dd.rectangle((W // 2 + 2, y, W // 2 + 8, H), fill=(255, 255, 255, int(40 * (1 - e))))
            return c
        if bi == 0 and lokal < 1.8:
            e = ease(lokal / 1.6)
            c = self.kertas.copy()
            c.paste(cur, (0, int((1 - e) * H * 0.55)))
            return c
        return cur

    def over2(self, d, ov, bi, p, lokal, pg, t):
        b = self.b[bi]
        self.aman("judul", self.judul_layar, d, bi, lokal)
        if b.get("dalil") and lokal > 1.5:
            self.aman("dalil", self.dalil, d, b["dalil"], lokal - 1.5)
        elif b.get("teks_layar") and lokal > 1.2:
            self.aman("banner", self.banner, d, b["teks_layar"][0], lokal - 1.2)
        if b.get("kitab") and lokal > 1.5:
            self.aman("kitab", self.kitab, d, b["kitab"], lokal - 1.5)
        k = self.kalimat_kini(t)
        if k:
            font = F("bold", 34)
            kata = k.split()
            baris, _ = tata_kata(d, kata, font, 600)
            tinggi = len(baris) * 46 + 28
            y0 = H - 250
            d.rounded_rectangle((40, y0 - 14, W - 40, y0 + tinggi), 20, fill=KREM + (225,), outline=EMAS + (255,), width=3)
            blok(d, W // 2, y0, k, font, 600, COKLAT + (255,), None, 0, lh=46)

    def banner(self, d, teks, q):
        a = int(255 * ease(q / 0.5))
        font = F("bold", 46)
        tw = clamp(d.textlength(teks, font=font) + 80, 260, 660)
        d.rounded_rectangle((W / 2 - tw / 2, 200, W / 2 + tw / 2, 300), 16, fill=KREM + (int(a * 0.92),),
                            outline=EMAS + (a,), width=8)
        blok(d, W // 2, 222, teks, font, tw - 40, COKLAT + (a,), None, 0, lh=56)

    def dalil(self, d, dl, q):
        a = int(255 * ease(q / 0.6))
        arab = str(dl.get("arab", "")).strip()
        arti = str(dl.get("arti", "")).strip()
        ruj = str(dl.get("rujukan", "")).strip()
        fa, ft, fr = F("arab", 62), F("bold", 30), F("reg", 24)
        baris_ar = baris_arab(d, arab, fa, 560)
        h_ar = len(baris_ar) * 100
        arti_baris, _ = tata_kata(d, arti.split(), ft, 560)
        h_arti = len(arti_baris) * 42
        total = 40 + h_ar + 24 + h_arti + (40 if ruj else 0) + 20
        y0 = clamp(330 - total / 2 + 120, 140, 400)
        d.rounded_rectangle((40, y0, W - 40, y0 + total), 26, fill=KREM + (int(a * 0.94),), outline=EMAS + (a,), width=10)
        y = y0 + 30
        for s in baris_ar:
            tulis_ar(d, (W // 2, y), s, fa, COKLAT + (a,))
            y += 100
        d.line((120, y + 4, W - 120, y + 4), fill=EMAS + (a,), width=3)
        y += 22
        h = sorot_latar(d, W // 2, y, arti, ft, 560, dl.get("kata_kunci"), (255, 215, 90, a), COKLAT + (a,), lh=42)
        if ruj:
            d.text((W // 2, y + h + 6), ruj[:70], font=fr, fill=(120, 95, 60, a), anchor="mt")

    def kitab(self, d, kitab, q):
        for i, k in enumerate(kitab[:2]):
            a = int(255 * ease((q - i * 0.5) / 0.6))
            if a <= 0:
                continue
            x0 = 30 + i * 340
            d.rounded_rectangle((x0, 300, x0 + 320, 700), 16, fill=KREM + (int(a * 0.94),), outline=EMAS + (a,), width=6)
            d.text((x0 + 160, 330), str(k.get("nama", ""))[:34], font=F("bold", 26), fill=COKLAT + (a,), anchor="mt")
            d.line((x0 + 30, 372, x0 + 290, 372), fill=EMAS + (a,), width=3)
            blok(d, x0 + 160, 390, k.get("isi", ""), F("reg", 26), 270, COKLAT + (a,), None, 0, lh=36)

    # ============================= MODE 3
    BAR_ATAS, BAR_BAWAH = 140, 220

    def base3(self, bi, p, lokal, pg, t):
        c = Image.new("RGB", (W, H), (0, 0, 0))
        tinggi = H - self.BAR_ATAS - self.BAR_BAWAH
        c.paste(cover(self.img[bi], W, tinggi, 1 + 0.03 * p), (0, self.BAR_ATAS))
        return c

    def over3(self, d, ov, bi, p, lokal, pg, t):
        b = self.b[bi]
        if bi == 1:
            self.aman("grid", self.grid_blueprint, d)
        d.rectangle((0, 0, W, self.BAR_ATAS), fill=(0, 0, 0, 255))
        d.rectangle((0, H - self.BAR_BAWAH, W, H), fill=(0, 0, 0, 255))
        pov = self.c.get("pov_label") or "POV - Kamu Adalah Pemilik Usaha"
        d.text((W // 2, 70), pov, font=F("bold", 24), fill=(255, 255, 255, 255), anchor="mm")
        self.aman("judul", self.judul_layar, d, bi, lokal)
        tabel_bawah = 190
        if b.get("tabel") and lokal > 0.8:
            tabel_bawah = self.aman_ret("tabel", self.tabel, d, b["tabel"], lokal - 0.8, 190) or 190
        if b.get("mitos_realita") and lokal > 2.0:
            self.aman("mitos", self.mitos, d, b["mitos_realita"], lokal - 2.0, max(tabel_bawah + 24, 620))
        if b.get("grafik") and lokal > 1.0:
            self.aman("grafik", self.grafik, d, b["grafik"], p, lokal)
        k = self.kalimat_kini(t)
        if k:
            blok_warna(d, W // 2, H - self.BAR_BAWAH + 36, k, F("bold", 34), 640, self.b[bi].get("sorot"),
                       [(255, 90, 170, 255), (255, 225, 0, 255)], (255, 255, 255, 255), 2, (0, 0, 0, 255), lh=44)

    def aman_ret(self, nama, fn, *a):
        try:
            return fn(*a)
        except Exception as e:
            if nama not in self.lapor:
                self.lapor.add(nama)
                log(f"[render] elemen '{nama}' dilewati: {e}")
            return None

    def grid_blueprint(self, d):
        for x in range(0, W, 48):
            d.line((x, self.BAR_ATAS, x, H - self.BAR_BAWAH), fill=(120, 190, 255, 55), width=1)
        for y in range(self.BAR_ATAS, H - self.BAR_BAWAH, 48):
            d.line((0, y, W, y), fill=(120, 190, 255, 55), width=1)

    def tabel(self, d, tb, q, y0):
        baris = (tb.get("baris") or [])[:7]
        rh = 46
        tinggi = 58 + len(baris) * rh + 12
        a0 = int(255 * ease(q / 0.4))
        d.rounded_rectangle((30, y0, W - 30, y0 + tinggi), 14, fill=(8, 28, 70, int(a0 * 0.9)),
                            outline=(120, 190, 255, a0), width=3)
        d.text((W // 2, y0 + 30), str(tb.get("judul", "")).upper()[:46], font=F("bold", 26),
               fill=(255, 225, 0, a0), anchor="mm")
        for i, r in enumerate(baris):
            qa = q - 0.4 - i * 0.55
            if qa <= 0:
                continue
            a = int(255 * ease(qa / 0.3))
            y = y0 + 58 + i * rh
            label, nilai = str(r[0]), str(r[1]) if len(r) > 1 else ""
            penting = label.lower().startswith(("total", "sisa", "bep", "laba", "untung"))
            warna = (255, 225, 0, a) if penting else (255, 255, 255, a)
            d.line((50, y, W - 50, y), fill=(120, 190, 255, int(a * 0.5)), width=1)
            d.text((54, y + rh // 2), label[:30], font=F("bold", 27), fill=warna, anchor="lm")
            d.text((W - 54, y + rh // 2), animasi_angka(nilai, qa / 0.9)[:30], font=F("bold", 27), fill=warna, anchor="rm")
        return y0 + tinggi

    def mitos(self, d, mr, q, y0):
        a = int(255 * ease(q / 0.5))
        for i, (judul, isi, warna) in enumerate([("MITOS", mr.get("mitos", ""), (60, 190, 100)),
                                                  ("REALITA", mr.get("realita", ""), (200, 45, 45))]):
            x0 = 30 + i * 345
            d.rounded_rectangle((x0, y0, x0 + 315, y0 + 230), 16, fill=warna + (int(a * 0.93),),
                                outline=(255, 255, 255, a), width=3)
            d.text((x0 + 157, y0 + 30), judul, font=F("bold", 30), fill=(255, 255, 255, a), anchor="mm")
            blok(d, x0 + 157, y0 + 62, isi, F("bold", 28), 285, (255, 255, 255, a), (0, 0, 0, int(a * 0.6)), 2, lh=36)

    def grafik(self, d, g, p, lokal):
        xs, ys = list(g.get("x") or []), [float(v) for v in (g.get("y") or [])]
        if len(ys) < 2:
            return
        a = int(255 * ease((lokal - 1.0) / 0.5))
        x0, x1, y0, y1 = 120, W - 60, 260, 600
        d.rounded_rectangle((30, 190, W - 30, 760), 16, fill=(8, 28, 70, int(a * 0.92)), outline=(120, 190, 255, a), width=3)
        d.text((W // 2, 222), str(g.get("judul", ""))[:44], font=F("bold", 26), fill=(255, 225, 0, a), anchor="mm")
        d.line((x0, y0, x0, y1), fill=(255, 255, 255, a), width=4)  # sumbu Y
        d.line((x0, y1, x1, y1), fill=(255, 255, 255, a), width=4)  # sumbu X
        lo, hi = min(0.0, min(ys)), max(ys) * 1.1 or 1
        titik = []
        for i, v in enumerate(ys):
            x = x0 + 20 + i * (x1 - x0 - 40) / (len(ys) - 1)
            y = y1 - (v - lo) / (hi - lo) * (y1 - y0 - 20)
            titik.append((x, y))
            if i < len(xs):
                d.text((x, y1 + 18), str(xs[i])[:10], font=F("reg", 20), fill=(255, 255, 255, a), anchor="mm")
        d.text((x0 - 8, y0), f"{hi:,.0f}".replace(",", "."), font=F("reg", 18), fill=(255, 255, 255, a), anchor="rm")
        d.text((x0 - 8, y1), f"{lo:,.0f}".replace(",", "."), font=F("reg", 18), fill=(255, 255, 255, a), anchor="rm")
        d.text((x0 - 20, y0 - 14), str(g.get("y_label", ""))[:18], font=F("reg", 20), fill=(190, 220, 255, a), anchor="lm")
        d.text((x1, y1 + 50), str(g.get("x_label", ""))[:20], font=F("reg", 20), fill=(190, 220, 255, a), anchor="rm")
        prog = clamp((lokal - 1.4) / 3.0) * (len(titik) - 1)
        for i in range(len(titik) - 1):
            if prog >= i + 1:
                d.line((*titik[i], *titik[i + 1]), fill=(235, 50, 50, 255), width=8)
            elif prog > i:
                f = prog - i
                tx = titik[i][0] + (titik[i + 1][0] - titik[i][0]) * f
                ty = titik[i][1] + (titik[i + 1][1] - titik[i][1]) * f
                d.line((*titik[i], tx, ty), fill=(235, 50, 50, 255), width=8)
        for i, (x, y) in enumerate(titik):
            if prog >= i:
                d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(235, 50, 50, 255), outline=(255, 255, 255, 255), width=2)
        if g.get("teks_besar") and prog >= len(titik) - 1.01:
            blok(d, W // 2, 660, g["teks_besar"], F("bold", 52), 620, (255, 70, 70, 255), (255, 255, 255, 255), 3, lh=62)


# ------------------------------------------------------------------ rakit
def render_video(mode, cerita, gambar, batas, kalimat, total, wav, out_mp4):
    P = Perender(mode, cerita, gambar, batas, kalimat, total)
    n = int(math.ceil(total * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(wav)]
    musik = ROOT / "assets" / "musik" / f"mode{mode['id']}.mp3"
    if musik.exists():
        cmd += ["-stream_loop", "-1", "-i", str(musik), "-filter_complex",
                "[2:a]volume=0.10[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out_mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(P.frame(i / FPS).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg gagal merakit video")
    return out_mp4


def bikin_thumbnail(mode, cerita, gambar, out_jpg):
    idx = {"1": 0, "2": 1, "3": 0}[mode["id"]]
    im = cover(Image.open(gambar[idx]).convert("RGB"), W, H, 1.0)
    d = ImageDraw.Draw(im, "RGBA")
    teks = (cerita.get("thumbnail_teks") or (cerita.get("judul_pilihan") or [""])[0]).upper()
    if mode["id"] == "2":
        d.rounded_rectangle((40, 430, W - 40, 850), 24, fill=KREM + (225,), outline=EMAS + (255,), width=10)
        blok(d, W // 2, 470, teks, F("bold", 64), 600, COKLAT + (255,), None, 0, lh=82)
    else:
        blok(d, W // 2, 470, teks, F("bold", 72), 640, (255, 255, 255, 255), (0, 0, 0, 255), 8, lh=90)
    im.save(out_jpg, quality=90)
    return out_jpg
