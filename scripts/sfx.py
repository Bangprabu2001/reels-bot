"""Membuat efek suara sederhana (whoosh dan pop) sebagai file WAV, tanpa library tambahan."""
import math
import random
import struct
import wave
from pathlib import Path

LAJU = 22050


def _tulis(path: Path, sampel) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(LAJU)
        w.writeframes(
            b"".join(struct.pack("<h", int(max(-1.0, min(1.0, x)) * 32767)) for x in sampel)
        )


def _whoosh():
    n = int(0.5 * LAJU)
    acak = random.Random(7)
    lp = 0.0
    keluar = []
    for i in range(n):
        t = i / n
        env = math.sin(math.pi * t) ** 2  # naik lalu turun
        a = 0.02 + 0.6 * t  # filter makin terbuka: nada "menyapu" naik
        lp += a * (acak.uniform(-1, 1) - lp)
        keluar.append(lp * env * 2.2)
    return keluar


def _pop():
    n = int(0.14 * LAJU)
    fase = 0.0
    keluar = []
    for i in range(n):
        t = i / n
        fase += 2 * math.pi * (700 - 450 * t) / LAJU  # nada turun cepat
        keluar.append(math.sin(fase) * math.exp(-6 * t) * 0.8)
    return keluar


def buat_sfx(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    _tulis(folder / "whoosh.wav", _whoosh())
    _tulis(folder / "pop.wav", _pop())
