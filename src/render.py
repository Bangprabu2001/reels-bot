"""Render video kuis memakai template milik user (1080x1920)."""
import json
import math
import os
import subprocess
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from .common import ROOT, log
from .penulis import ANGKA_KATA

W, H, FPS = 1080, 1920, 24
AS = ROOT / "assets"
TPL = Image.open(AS / "template" / "template.png").convert("RGB")
TPL_BG = Image.open(AS / "template" / "latar.png").convert("RGB")
MASK = Image.open(AS / "template" / "mask.png").convert("L")
FB, FM = str(AS / "fonts" / "Poppins-Bold.ttf"), str(AS / "fonts" / "Poppins-Medium.ttf")
CX, PIL_ATAS, PIL_BAWAH = 537, (537, 340), (531, 1407)
MERAH, GELAP, ABU = (200, 16, 20), (38, 14, 14), (120, 100, 100)

_f = {}
def F(sz, tebal=True):
    k = (sz, tebal)
    if k not in _f:
        _f[k] = ImageFont.truetype(FB if tebal else FM, sz)
    return _f[k]
def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def wrap(d, teks, font, mw):
    out, cur = [], ""
    for w in str(teks).split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= mw: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out
def fit(d, teks, mx, mn, mw, tebal=True):
    for sz in range(mx, mn - 1, -2):
        if d.textlength(teks, font=F(sz, tebal)) <= mw: return F(sz, tebal)
    return F(mn, tebal)
def para(d, cx, cy, teks, font, mw, fill, lh=None):
    ls = wrap(d, teks, font, mw); lh = lh or int(font.size * 1.28)
    y = cy - (len(ls) - 1) * lh / 2
    for i, l in enumerate(ls): d.text((cx, y + i * lh), l, font=font, fill=fill, anchor="mm")
    return len(ls) * lh


# ------------------------------------------------------------------ jadwal dinamis
def susun_jadwal(dur, cfg, paket):
    """Waktu tiap bagian mengikuti panjang suara narator, lalu dijaga di rentang 60-90 detik."""
    n = len(dur["soal"]); cd0 = int(cfg.get("hitung_mundur_detik", 4))
    dmin, dmaks = cfg.get("durasi_min_detik", 60), cfg.get("durasi_maks_detik", 90)

    def bangun(cd_default):
        t = max(3.2, dur["hook"] + 0.6); hook = t; J = []
        for i in range(n):
            soal = max(3.4, dur["soal"][i] + 0.7)                          # suara membaca soal, lalu hitung mundur
            cd = cd_default + 1 if i == n - 1 else cd_default           # soal jebakan diberi waktu lebih
            baca_a2 = 0.9 + 0.22 * len(str(paket["soal"][i]["a2"]).split()) + 0.7   # waktu penonton membaca penjelasan
            ans = max(4.4, dur["jawab"][i] + 1.0, baca_a2)
            J.append(dict(i=i, s=t, soal=soal, cd=cd, ans=ans, e=t + soal + cd + ans)); t += soal + cd + ans
        reward = t; r = dur["intro"] + 0.7; baris = [0.0] * 4
        for k in (3, 2, 1, 0):
            baris[k] = r; r += dur["baris"][k] + 0.7
        penutup_t = r; r += dur["penutup"] + 1.0
        return dict(hook=hook, soal=J, reward=reward, baris=baris, penutup_t=penutup_t, total=reward + r, cd=cd_default)
    cd = cd0; jad = bangun(cd)
    while jad["total"] > dmaks and cd > 2:
        cd -= 1; jad = bangun(cd)
    while jad["total"] < dmin and cd < 8:
        cd += 1; jad = bangun(cd)
    jad["catatan"] = None
    if jad["total"] > dmaks: jad["catatan"] = f"Durasi {jad['total']:.0f} detik melebihi {dmaks} detik (soal/penjelasan terlalu panjang)."
    if jad["total"] < dmin: jad["catatan"] = f"Durasi {jad['total']:.0f} detik kurang dari {dmin} detik."
    ev = [(0.0, 0.10)]
    for J in jad["soal"]:
        ev.append((J["s"], 0.08)); ev += [(J["s"] + J["soal"] + k, 0.07) for k in range(int(J["cd"]))]
        ev.append((J["s"] + J["soal"] + J["cd"], 0.22))
    ev += [(jad["reward"] + jad["baris"][k], 0.12) for k in range(1, 4)] + [(jad["reward"] + jad["baris"][0], 0.25)]
    jad["denyut"] = ev
    return jad


# ------------------------------------------------------------------ logo / watermark (config/branding.json)
def _muat_brand(item, kotak, tinggi_maks):
    if not item or not item.get("aktif", True): return None
    pth = ROOT / item.get("file", "")
    if item.get("file") and pth.exists(): im = Image.open(pth).convert("RGBA")
    elif item.get("teks"):
        f = ImageFont.truetype(FB, 64); tmp = Image.new("RGBA", (10, 10))
        w = int(ImageDraw.Draw(tmp).textlength(item["teks"], font=f)) + 20
        im = Image.new("RGBA", (w, 100), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((w // 2, 50), item["teks"], font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(90, 0, 0, 255))
    else: return None
    lebar = int(W * item.get("lebar_persen", 20) / 100); sk = min(lebar / im.width, tinggi_maks / im.height)
    im = im.resize((max(1, int(im.width * sk)), max(1, int(im.height * sk))), Image.LANCZOS)
    tr = item.get("transparansi", 100)
    if tr < 100: im.putalpha(im.getchannel("A").point(lambda v: int(v * tr / 100)))
    pos = item.get("posisi", "atas-tengah"); atas = pos.startswith("atas")
    z = kotak["atas"] if atas else kotak["bawah"]
    y = z[0] + (z[1] - z[0] - im.height) // 2
    x = {"kiri": 70, "tengah": (W - im.width) // 2, "kanan": W - 70 - im.width}.get(pos.split("-")[-1], (W - im.width) // 2)
    return im, (x, y)

def _brand():
    try: cfg = json.load(open(ROOT / "config" / "branding.json", encoding="utf-8"))
    except Exception: return []
    kotak = {"atas": (85, 265), "bawah": (1490, 1640)}
    out = []
    for nama in ("logo", "watermark"):
        b = _muat_brand(cfg.get(nama), kotak, 170 if nama == "logo" else 110)
        if b: out.append(b)
    return out


_YY, _XX = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
_PROJ = _XX * 4 * 0.80 + _YY * 4 * 0.60
_rng = np.random.default_rng(11)
PART = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(25, 70), _rng.uniform(5, 15), _rng.uniform(0, 6.28), _rng.uniform(40, 110)) for _ in range(34)]


class Perender:
    def __init__(self, paket, jad):
        self.soal, self.gelar, self.jad = paket["soal"], paket["gelar"], jad
        self.n = len(self.soal); self.brand = _brand()
        self.lab = [f"{self.n}/{self.n}", f"{self.n - 1}/{self.n}", f"{self.n - 2}/{self.n}", f"0-{self.n - 3}"]

    # ---------- latar bergerak
    def denyut(self, t):
        return sum(a * math.exp(-(t - te) / 0.22) for te, a in self.jad["denyut"] if t >= te)

    def fondo(self, t):
        sk = 1.0 + 0.065 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 8.0))
        nw, nh = int(W * sk) + 2, int(H * sk) + 2
        z = TPL_BG.resize((nw, nh), Image.BILINEAR)
        ox = int((nw - W) * (0.5 + 0.5 * math.sin(2 * math.pi * t / 11.0)))
        oy = int((nh - H) * (0.5 + 0.5 * math.cos(2 * math.pi * t / 13.0)))
        bg = ImageEnhance.Brightness(z.crop((ox, oy, ox + W, oy + H))).enhance(1.0 + min(0.35, self.denyut(t)))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for (cx, cy) in ((60, 140), (1020, 1780)):
            for k in range(3):
                r = ((t * 110 + k * 150) % 450) + 40; al = int(110 * (1 - r / 500))
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, max(0, al)), width=5)
        for (x0, y0, sp, sz, ph, al) in PART:
            x = (x0 + 30 * math.sin(t * 0.8 + ph)) % W; y = (y0 - sp * t) % H
            d.ellipse((x - sz, y - sz, x + sz, y + sz), fill=(255, 235, 200, int(al * (0.6 + 0.4 * math.sin(t * 2 + ph)))))
        bg = Image.alpha_composite(bg.convert("RGBA"), ov)
        pos = ((t % 5.0) / 5.0) * 2600 - 700
        band = (np.exp(-((_PROJ - pos) / 110.0) ** 2) * 75).astype(np.uint8)
        sweep = Image.merge("RGBA", [Image.new("L", band.shape[::-1], 255)] * 3 + [Image.fromarray(band, "L")]).resize((W, H), Image.BILINEAR)
        return Image.composite(TPL, Image.alpha_composite(bg, sweep).convert("RGB"), MASK)

    # ---------- elemen
    def titik(self, d, y, aktif, penuh):
        for i in range(self.n):
            x = CX + (i - (self.n - 1) / 2) * 76
            if i < aktif or (i == aktif and penuh): d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=MERAH + (255,))
            elif i == aktif: d.ellipse((x - 20, y - 20, x + 20, y + 20), outline=MERAH + (255,), width=6)
            else: d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=(215, 205, 205, 255))

    def pita(self, d, atas=None, bawah=None, t=0):
        if atas: d.text(PIL_ATAS, atas, font=fit(d, atas, 56, 34, 620), fill=(255, 255, 255, 255), anchor="mm")
        if bawah:
            p = 1 + 0.03 * math.sin(t * 7)
            d.text(PIL_BAWAH, bawah, font=fit(d, bawah, int(46 * p), 30, 600), fill=(255, 255, 255, 255), anchor="mm")

    def frame(self, t):
        J, n = self.jad, self.n
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        if t < J["hook"]:
            self.pita(d, "TANTANGAN OTAK", "Skor penuh = gelar langka", t)
            for k, (txt, mx, y) in enumerate([(f"JAWAB {n}", 190, 700), ("TEKA-TEKI", 150, 880)]):
                e = ease((t - 0.1 - k * 0.2) / 0.35)
                d.text((CX, y + (1 - e) * 60), txt, font=fit(d, txt, mx, 60, 800), fill=MERAH + (int(255 * e),), anchor="mm")
            e = ease((t - 0.8) / 0.4)
            d.text((CX, 1060 + (1 - e) * 40), "Lihat nilaimu di akhir!", font=fit(d, "Lihat nilaimu di akhir!", 68, 40, 800), fill=GELAP + (int(255 * e),), anchor="mm")
            self.titik(d, 1250, -1, False)
        elif t < J["reward"]:
            S = next(x for x in J["soal"] if x["s"] <= t < x["e"]); i = S["i"]; l = t - S["s"]
            q, a, a2 = self.soal[i]["q"], self.soal[i]["a"], self.soal[i]["a2"]
            if l < S["soal"]:
                self.pita(d, f"SOAL {i + 1} / {n}", "Jawab dulu di kepala!", t)
                e = ease(l / 0.35)
                para(d, CX, 820 + (1 - e) * 50, q, F(88), 780, GELAP + (int(255 * e),), 118)
                self.titik(d, 1262, i, False)
            elif l < S["soal"] + S["cd"]:
                self.pita(d, f"SOAL {i + 1} / {n}", "Tulis jawabanmu di komentar!", t)
                lc = l - S["soal"]
                para(d, CX, 640, q, F(64), 800, GELAP + (255,), 86)
                sisa = S["cd"] - lc; ang = int(math.ceil(sisa)); frac = sisa / S["cd"]
                cx, cy, r = CX, 1030, 165
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(225, 210, 210, 255), width=26)
                d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=MERAH + (255,), width=26)
                sc = 1 + 0.16 * (1 - (sisa % 1))
                d.text((cx, cy - 6), str(ang), font=F(int(210 * sc)), fill=MERAH + (255,), anchor="mm")
                self.titik(d, 1262, i, False)
            else:
                la = l - S["soal"] - S["cd"]
                self.pita(d, f"SOAL {i + 1} / {n}", "Benar? Tambah 1 poin!", t)
                e = ease(la / 0.4)
                para(d, CX, 590, q, F(50), 800, ABU + (255,), 68)
                d.text((CX, 760 - (1 - e) * 20), "JAWABANNYA", font=F(46), fill=MERAH + (int(255 * e),), anchor="mm")
                fa = F(78); ls = wrap(d, a, fa, 740); h = len(ls) * 100 + 56
                y0 = 820 + int((1 - e) * 80)
                d.rounded_rectangle((CX - 400, y0, CX + 400, y0 + h), 34, fill=MERAH + (int(255 * e),))
                para(d, CX, y0 + h / 2, a, fa, 740, (255, 255, 255, 255), 100)
                if la > 0.9:
                    e2 = ease((la - 0.9) / 0.5)
                    para(d, CX, y0 + h + 120, a2, F(42, False), 780, GELAP + (int(255 * e2),), 58)
                self.titik(d, 1262, i, True)
                k = 1 - la / 0.18
                if 0 < k < 1: d.rectangle((90, 450, 985, 1345), fill=(255, 255, 255, int(150 * k)))
        else:
            l = t - J["reward"]
            self.pita(d, "HASIL AKHIR", None)
            e = ease(l / 0.4)
            d.text((CX, 520 - (1 - e) * 30), "BENAR BERAPA?", font=fit(d, "BENAR BERAPA?", 84, 50, 780), fill=MERAH + (int(255 * e),), anchor="mm")
            d.text((CX, 590), "Ini gelarmu:", font=F(40, False), fill=GELAP + (int(255 * e),), anchor="mm")
            for k in range(4):
                tk = J["baris"][k]; e = ease((l - tk) / 0.45)
                if e <= 0: continue
                y = 735 + k * 170 - (1 - e) * 40; best = (k == 0); al = int(255 * e)
                g = self.gelar[k]
                d.rounded_rectangle((115, y - 72, 960, y + 72), 30, fill=(255, 214, 60, al) if best else (255, 232, 232, al), outline=MERAH + (al,), width=6 if best else 4)
                d.ellipse((138, y - 54, 246, y + 54), fill=MERAH + (al,))
                d.text((192, y), self.lab[k], font=F(40), fill=(255, 255, 255, al), anchor="mm")
                nama = str(g["nama"]).upper()
                d.text((272, y - 20), nama, font=fit(d, nama, 42, 26, 640), fill=GELAP + (al,), anchor="lm")
                tg = str(g["tagline"])
                d.text((272, y + 28), tg, font=fit(d, tg, 30, 20, 640, False), fill=(90, 50, 50, al), anchor="lm")
                if best and 0 < (l - tk) < 0.2: d.rectangle((90, 450, 985, 1345), fill=(255, 255, 255, int(150 * (1 - (l - tk) / 0.2))))
            self.pita(d, None, "Lihat skormu di atas!" if l < J["baris"][0] else "Tulis gelarmu di komentar!", t)
        out = Image.alpha_composite(self.fondo(t).convert("RGBA"), ov)
        for im, xy in self.brand: out.alpha_composite(im, xy)
        return out.convert("RGB")


_PR = None
def _frame_i(i):
    return _PR.frame(i / FPS).tobytes()


def render_video(paket, jad, wav, out_mp4):
    """Render paralel (semua inti CPU), frame dikirim berurutan ke ffmpeg."""
    global _PR
    _PR = Perender(paket, jad)
    n = int(jad["total"] * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
           "-shortest", "-movflags", "+faststart", str(out_mp4)]
    proses = max(1, min(4, os.cpu_count() or 1))
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        if proses > 1:
            with Pool(proses) as pool:
                for b in pool.imap(_frame_i, range(n), chunksize=6):
                    p.stdin.write(b)
        else:
            for i in range(n): p.stdin.write(_frame_i(i))
    finally:
        p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg gagal merakit video")
    return out_mp4


def bikin_thumbnail(paket, jad, out_jpg):
    pr = Perender(paket, jad)
    pr.frame(1.6).save(out_jpg, quality=90)
    return out_jpg
