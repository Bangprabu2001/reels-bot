"""Membuat efek suara (whoosh, pop, ding, tick, rustle, ketik) sebagai file WAV tanpa library tambahan.

Kalau kamu menaruh file sendiri di public/sfx/ dengan nama whoosh.mp3 / pop.mp3 / ding.mp3
(atau .wav/.ogg), file itu yang dipakai dan menggantikan suara buatan kode.
Efek suara gratis berkualitas bisa diunduh dari Pixabay (Sound Effects).
"""
import math
import random
import struct
import wave
from pathlib import Path

LAJU = 22050
NAMA = ("whoosh", "pop", "ding", "tick", "rustle", "ketik")


def _normal(sampel, puncak=0.9):
    m = max((abs(x) for x in sampel), default=1.0) or 1.0
    return [x / m * puncak for x in sampel]


def _tulis(path: Path, sampel) -> None:
    sampel = _normal(sampel)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(LAJU)
        w.writeframes(b"".join(struct.pack("<h", int(x * 32767)) for x in sampel))


def _gema(sampel, jeda=0.045, umpan=0.3, ulang=3):
    """Gema ringan supaya suara tidak terlalu kering."""
    d = int(jeda * LAJU)
    keluar = list(sampel) + [0.0] * (d * ulang)
    for i in range(len(keluar)):
        if i >= d:
            keluar[i] += keluar[i - d] * umpan
    return keluar


def _whoosh():
    n = int(0.55 * LAJU)
    acak = random.Random(11)
    cepat = lambat = 0.0
    keluar = []
    for i in range(n):
        t = i / n
        env = math.sin(math.pi * t ** 0.7) ** 2  # puncak lebih awal, lalu menghilang halus
        x = acak.uniform(-1, 1)
        cepat += (0.03 + 0.45 * t) * (x - cepat)  # penyaring yang makin terbuka: nada menyapu naik
        lambat += 0.02 * (x - lambat)
        keluar.append((cepat - lambat) * env)
    return _gema(keluar)


def _pop():
    n = int(0.16 * LAJU)
    acak = random.Random(3)
    fase = 0.0
    keluar = []
    for i in range(n):
        t = i / LAJU
        fase += 2 * math.pi * (380 + 520 * min(1.0, t / 0.05)) / LAJU  # nada naik cepat, seperti gelembung
        v = math.sin(fase) * math.exp(-t * 28)
        if i < 30:
            v += acak.uniform(-1, 1) * 0.3 * (1 - i / 30)  # klik kecil di awal
        keluar.append(v)
    return keluar


def _ding():
    n = int(0.9 * LAJU)
    keluar = [0.0] * n
    for f, mulai in ((1318.5, 0.0), (1760.0, 0.06), (2093.0, 0.12)):  # tiga nada naik: kilau
        o = int(mulai * LAJU)
        for i in range(n - o):
            t = i / LAJU
            keluar[o + i] += (
                math.sin(2 * math.pi * f * t) + 0.3 * math.sin(2 * math.pi * f * 2.01 * t)
            ) * math.exp(-t * 5.5)
    return keluar


def _tick():
    """Detak digital halus (gaya HUD)."""
    n = int(0.06 * LAJU)
    keluar = []
    for i in range(n):
        t = i / LAJU
        keluar.append(
            math.sin(2 * math.pi * 3200 * t) * math.exp(-t * 160) * 0.7
            + math.sin(2 * math.pi * 1600 * t) * math.exp(-t * 90) * 0.4
        )
    return keluar


def _rustle():
    """Gemerisik kertas (gaya Kertas)."""
    n = int(0.4 * LAJU)
    acak = random.Random(5)
    langkah = max(1, int(0.012 * LAJU))
    lp = amp = 0.0
    keluar = []
    for i in range(n):
        if i % langkah == 0:
            amp = acak.random() ** 2
        x = acak.uniform(-1, 1)
        lp += 0.15 * (x - lp)
        keluar.append((x - lp) * amp * (1 - i / n) ** 1.5)
    return keluar


def _ketik():
    """Ketikan mesin tik (gaya Noir)."""
    n = int(0.09 * LAJU)
    acak = random.Random(9)
    keluar = []
    for i in range(n):
        t = i / LAJU
        klik = acak.uniform(-1, 1) * math.exp(-t * 220)
        dug = math.sin(2 * math.pi * 180 * t) * math.exp(-t * 60) * 0.8
        keluar.append(klik * 0.7 + dug)
    return keluar


def buat_sfx(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    _tulis(folder / "whoosh.wav", _whoosh())
    _tulis(folder / "pop.wav", _pop())
    _tulis(folder / "ding.wav", _ding())
    _tulis(folder / "tick.wav", _tick())
    _tulis(folder / "rustle.wav", _rustle())
    _tulis(folder / "ketik.wav", _ketik())


def peta_sfx(public: Path) -> dict:
    """Nama efek -> file di public/. File buatan sendiri (mp3/ogg) didahulukan dari WAV buatan kode."""
    hasil = {}
    for nama in NAMA:
        for ext in ("mp3", "ogg", "wav"):
            if (public / "sfx" / f"{nama}.{ext}").exists():
                hasil[nama] = f"sfx/{nama}.{ext}"
                break
    return hasil
