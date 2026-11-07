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


def muat(d, teks, mx, mn, mw, mh, tebal=True, kl=1.28):
    """Font terbesar yang membuat teks terbungkus muat di lebar mw DAN tinggi mh. Mengembalikan (font, baris, lh)."""
    for sz in range(mx, mn - 1, -2):
        f = F(sz, tebal); ls = wrap(d, teks, f, mw); lh = int(sz * kl)
        if len(ls) * lh <= mh and all(d.textlength(l, font=f) <= mw + 2 for l in ls):
            return f, ls, lh
    f = F(mn, tebal); ls = wrap(d, teks, f, mw); lh = int(mn * kl)
    maks = max(1, mh // lh)
    if len(ls) > maks:
        ls = ls[:maks]; ls[-1] = ls[-1].rstrip(".,;:") + "…"
    return f, ls, lh
def tulis(d, cx, y, ls, f, lh, fill, anchor="mt"):
    for i, l in enumerate(ls): d.text((cx, y + i * lh), l, font=f, fill=fill, anchor=anchor)
    return len(ls) * lh


# ------------------------------------------------------------------ jadwal dinamis
def susun_jadwal(dur, cfg, paket):
    """Waktu tiap bagian mengikuti suara narator + waktu berpikir yang LEGA. Durasi video bebas (yang penting nyaman)."""
    jenis, n = paket["jenis"], len(paket["soal"]); skor = jenis != "psiko"
    wt = float(cfg.get("waktu_berpikir", {}).get(jenis, 10)); tambah = float(cfg.get("tambahan_soal_terakhir", 4))
    t = max(3.8, dur["hook"] + 0.8); hook = t; J = []
    for i in range(n):
        soal = max(3.8, dur["soal"][i] + 1.2)
        cd = wt + (tambah if jenis in ("teka", "logika") and i == n - 1 else 0)
        ans = 0.0
        if skor:
            baca = 1.6 + 0.30 * len(str(paket["soal"][i].get("a2", "")).split())
            ans = max(5.0, dur["jawab"][i] + 1.6, baca)
        J.append(dict(i=i, s=t, soal=soal, cd=cd, ans=ans, e=t + soal + cd + ans)); t += soal + cd + ans
    reward = t; r = dur["intro"] + 0.8
    nb = len(dur["baris"]); urut = list(range(nb - 1, -1, -1)) if skor else list(range(nb))
    baris = [0.0] * nb
    for k in urut:
        baris[k] = r; r += dur["baris"][k] + 0.9
    penutup_t = r; r += dur["penutup"] + 1.2
    seg = []
    for i in range(n):          # jendela waktu tiap bagian suara soal (untuk menyorot pilihan psikologi)
        w, c = [], 0.3
        for d_ in dur["soal_seg"][i]:
            w.append((c, c + d_)); c += d_ + 0.45
        seg.append(w)
    jad = dict(hook=hook, soal=J, reward=reward, baris=baris, urut=urut, penutup_t=penutup_t, total=reward + r, seg=seg, cd=wt)
    jad["catatan"] = (f"Durasi {jad['total']:.0f} detik, cukup panjang. Platform tertentu membatasi durasi Reels/Shorts." if jad["total"] > float(cfg.get("durasi_peringatan_detik", 180)) else None)
    ev = [(0.0, 0.10)]
    for x in J:
        ev.append((x["s"], 0.08)); ev += [(x["s"] + x["soal"] + k, 0.07) for k in range(int(x["cd"]))]
        if skor: ev.append((x["s"] + x["soal"] + x["cd"], 0.22))
    ev += [(reward + baris[k], 0.12) for k in urut] 
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


HOOK = {
    "tebak": ("TANTANGAN OTAK", "JAWAB {n}", "TEBAK-TEBAKAN", "Lihat nilaimu di akhir!", "Skor penuh = level tertinggi"),
    "teka": ("TANTANGAN OTAK", "JAWAB {n}", "TEKA-TEKI", "Lihat nilaimu di akhir!", "Skor penuh = level tertinggi"),
    "logika": ("UJI LOGIKAMU", "{n} SOAL", "TES LOGIKA", "Lihat levelmu di akhir!", "Kerjakan tanpa kalkulator"),
    "psiko": ("KENALI DIRIMU", "{n} PERTANYAAN", "TES PSIKOLOGI", "Hasilnya ada di akhir!", "Hiburan, bukan diagnosis"),
}
Z_ATAS, Z_BAWAH, LEBAR = 480, 1225, 800      # zona isi di dalam kotak putih (di atas titik progres)


class Perender:
    def __init__(self, paket, jad):
        self.p, self.jad = paket, jad
        self.soal, self.baris, self.jenis = paket["soal"], paket["baris"], paket["jenis"]
        self.n = len(self.soal); self.skor = self.jenis != "psiko"; self.brand = _brand()

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

    # ---------- elemen umum
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
            d.text(PIL_BAWAH, bawah, font=fit(d, bawah, int(46 * p), 28, 600), fill=(255, 255, 255, 255), anchor="mm")

    # ---------- layar hook
    def f_hook(self, d, t):
        atas, l1, l2, sub, bawah = HOOK[self.jenis]
        self.pita(d, atas, bawah, t)
        for k, (txt, mx, y) in enumerate([(l1.format(n=self.n), 170, 700), (l2, 140, 880)]):
            e = ease((t - 0.1 - k * 0.2) / 0.35)
            d.text((CX, y + (1 - e) * 60), txt, font=fit(d, txt, mx, 50, 800), fill=MERAH + (int(255 * e),), anchor="mm")
        e = ease((t - 0.8) / 0.4)
        d.text((CX, 1060 + (1 - e) * 40), sub, font=fit(d, sub, 66, 36, 800), fill=GELAP + (int(255 * e),), anchor="mm")
        self.titik(d, 1250, -1, False)

    # ---------- layar soal (tebak/teka/logika)
    def f_soal(self, d, S, i, l, t):
        q = str(self.soal[i]["q"]); n = self.n
        if l < S["soal"]:
            self.pita(d, f"SOAL {i + 1} / {n}", "Jawab dulu di kepala!", t)
            e = ease(l / 0.35); f, ls, lh = muat(d, q, 92, 40, LEBAR, 640)
            tulis(d, CX, (Z_ATAS + Z_BAWAH) / 2 - len(ls) * lh / 2 + (1 - e) * 50, ls, f, lh, GELAP + (int(255 * e),))
            self.titik(d, 1262, i, False)
        elif l < S["soal"] + S["cd"]:
            self.pita(d, f"SOAL {i + 1} / {n}", "Tulis jawabanmu di komentar!", t)
            lc = l - S["soal"]; f, ls, lh = muat(d, q, 64, 34, LEBAR, 330)
            tulis(d, CX, Z_ATAS + 10, ls, f, lh, GELAP + (255,))
            sisa = S["cd"] - lc; ang = int(math.ceil(sisa)); frac = sisa / S["cd"]
            cx, cy, r = CX, 1040, 150
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(225, 210, 210, 255), width=24)
            d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=MERAH + (255,), width=24)
            sc = 1 + 0.12 * (1 - (sisa % 1))
            d.text((cx, cy - 6), str(ang), font=F(int(190 * sc)), fill=MERAH + (255,), anchor="mm")
            self.titik(d, 1262, i, False)
        else:
            la = l - S["soal"] - S["cd"]
            self.pita(d, f"SOAL {i + 1} / {n}", "Benar? Tambah 1 poin!", t)
            self.f_jawab(d, q, str(self.soal[i]["a"]), str(self.soal[i].get("a2", "")), la)
            self.titik(d, 1262, i, True)
            k = 1 - la / 0.18
            if 0 < k < 1: d.rectangle((90, 450, 985, 1345), fill=(255, 255, 255, int(150 * k)))

    def f_jawab(self, d, q, a, a2, la):
        """Lembar jawaban: ukuran font otomatis mengecil sampai SEMUA teks muat di dalam kotak putih."""
        H_AVAIL = Z_BAWAH - Z_ATAS - 10
        for sk in [1.0, 0.92, 0.84, 0.76, 0.68, 0.6, 0.52, 0.46]:
            fq, lq, hq = muat(d, q, int(50 * sk), int(50 * sk), LEBAR, 9999, kl=1.3)
            fa, lA, ha = muat(d, a, int(78 * sk), int(78 * sk), 740, 9999, kl=1.28)
            fe, lE, he = muat(d, a2, int(42 * sk), int(42 * sk), LEBAR, 9999, False, 1.4) if a2.strip() else (None, [], 0)
            box = len(lA) * ha + 56
            total = len(lq) * hq + 26 + 52 + 14 + box + (30 + len(lE) * he if lE else 0)
            if total <= H_AVAIL: break
        e = ease(la / 0.4); y = Z_ATAS + 5 + (H_AVAIL - total) / 2
        tulis(d, CX, y, lq, fq, hq, ABU + (255,)); y += len(lq) * hq + 26
        d.text((CX, y + 22 - (1 - e) * 20), "JAWABANNYA", font=F(max(30, int(44 * sk))), fill=MERAH + (int(255 * e),), anchor="mm"); y += 52 + 14
        off = int((1 - e) * 70)
        d.rounded_rectangle((CX - 400, y + off, CX + 400, y + box + off), 34, fill=MERAH + (int(255 * e),))
        tulis(d, CX, y + 28 + off, lA, fa, ha, (255, 255, 255, 255)); y += box + 30
        if lE and la > 0.9:
            e2 = ease((la - 0.9) / 0.5)
            tulis(d, CX, y, lE, fe, he, GELAP + (int(255 * e2),))

    # ---------- layar tes psikologi
    def f_psiko(self, d, S, i, l, t):
        q = self.soal[i]["q"]; opsi = self.soal[i]["opsi"]; n = self.n
        lc = l - S["soal"]; tahap_cd = l >= S["soal"]
        self.pita(d, f"PERTANYAAN {i + 1} / {n}", "Catat pilihanmu: A, B, atau C!" if tahap_cd else "Baca semua pilihan dulu", t)
        e = ease(l / 0.35)
        fq, lq, hq = muat(d, q, 58, 36, LEBAR, 250)
        yq = Z_ATAS + 5 + (1 - e) * 40
        tulis(d, CX, yq, lq, fq, hq, GELAP + (int(255 * e),))
        y0 = Z_ATAS + 5 + len(lq) * hq + 34
        y_bar = y0
        if tahap_cd:  # bar waktu
            frac = max(0.0, 1 - lc / S["cd"]); sisa = int(math.ceil(S["cd"] - lc))
            d.rounded_rectangle((100, y0, 880, y0 + 22), 11, fill=(225, 210, 210, 255))
            d.rounded_rectangle((100, y0, 100 + int(780 * frac), y0 + 22), 11, fill=MERAH + (255,))
            d.text((940, y0 + 11), str(sisa), font=F(52), fill=MERAH + (255,), anchor="mm")
        y0 += 50
        tinggi_sedia = Z_BAWAH - y0
        for sk in [1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6]:
            fo = F(int(40 * sk)); lh = int(40 * sk * 1.28)
            bl = [wrap(d, opsi[h], fo, 640) for h in "ABC"]
            hs = [max(int(110 * sk), len(b) * lh + 40) for b in bl]
            if sum(hs) + 2 * 18 <= tinggi_sedia: break
        win = self.jad["seg"][i]; aktif = -1
        for k in range(3):
            if k + 1 < len(win) and win[k + 1][0] <= l < win[k + 1][1] + 0.2 and not tahap_cd: aktif = k
        y = y0
        for k, h in enumerate("ABC"):
            ea = ease((l - 0.5 - k * 0.15) / 0.3)
            if ea <= 0: y += hs[k] + 18; continue
            al = int(255 * ea); sel = (k == aktif)
            d.rounded_rectangle((100, y, 980, y + hs[k]), 26, fill=(255, 214, 60, al) if sel else (255, 236, 236, al), outline=MERAH + (al,), width=6 if sel else 4)
            cy = y + hs[k] / 2
            d.ellipse((124, cy - 42, 208, cy + 42), fill=MERAH + (al,))
            d.text((166, cy), h, font=F(48), fill=(255, 255, 255, al), anchor="mm")
            tulis(d, 240, cy - len(bl[k]) * lh / 2, bl[k], fo, lh, GELAP + (al,), anchor="lt")
            y += hs[k] + 18
        self.titik(d, 1262, i, False)

    # ---------- layar hasil / level
    def f_reward(self, d, t):
        J, n = self.jad, self.n; l = t - J["reward"]; e = ease(l / 0.4)
        if self.skor:
            judul, sub = "BENAR BERAPA?", "Ini levelmu:"
        else:
            judul, sub = "HASIL TESMU", "Pilihan yang paling sering kamu pilih:"
        self.pita(d, "HASIL AKHIR", None)
        d.text((CX, 520 - (1 - e) * 30), judul, font=fit(d, judul, 84, 50, 780), fill=MERAH + (int(255 * e),), anchor="mm")
        d.text((CX, 592), sub, font=fit(d, sub, 40, 26, 800, False), fill=GELAP + (int(255 * e),), anchor="mm")
        nb = len(self.baris)
        pitch, hh, y0 = (170, 76, 745) if nb == 4 else (228, 104, 758)
        for k in range(nb):
            tk = J["baris"][k]; ek = ease((l - tk) / 0.45)
            if ek <= 0: continue
            b = self.baris[k]; al = int(255 * ek); y = y0 + k * pitch - (1 - ek) * 40
            best = self.skor and k == 0
            nama = str(b["nama"]).upper(); mw = 650
            fn = fit(d, nama, 42, 26, mw)
            fd, ld, lhd = muat(d, str(b["deskripsi"]), 30, 22, mw, 80 if nb == 4 else 156, False, 1.3)
            tot = 48 + len(ld) * lhd
            half = min(max(hh, tot / 2 + 14), pitch / 2 - 6)
            d.rounded_rectangle((115, y - half, 965, y + half), 30, fill=(255, 214, 60, al) if best else (255, 232, 232, al), outline=MERAH + (al,), width=6 if best else 4)
            d.ellipse((138, y - 54, 246, y + 54), fill=MERAH + (al,))
            d.text((192, y), str(b["label"]), font=F(40 if len(str(b["label"])) > 1 else 56), fill=(255, 255, 255, al), anchor="mm")
            top = y - tot / 2
            d.text((272, top), nama, font=fn, fill=GELAP + (al,), anchor="lt")
            tulis(d, 272, top + 48, ld, fd, lhd, (90, 50, 50, al), anchor="lt")
            if best and 0 < (l - tk) < 0.2: d.rectangle((90, 450, 985, 1345), fill=(255, 255, 255, int(150 * (1 - (l - tk) / 0.2))))
        akhir = J["baris"][J["urut"][-1]]
        if self.skor: teks = "Lihat skormu di atas!" if l < akhir else "Tulis levelmu di komentar!"
        else: teks = "Seri? Ikut jawaban terakhir" if l < akhir else "Tulis tipemu di komentar!"
        self.pita(d, None, teks, t)

    def frame(self, t):
        J = self.jad
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        if t < J["hook"]:
            self.f_hook(d, t)
        elif t < J["reward"]:
            S = next(x for x in J["soal"] if x["s"] <= t < x["e"]); i = S["i"]; l = t - S["s"]
            (self.f_soal if self.skor else self.f_psiko)(d, S, i, l, t)
        else:
            self.f_reward(d, t)
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
