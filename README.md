# Pabrik Kuis

Tekan tombol di Telegram -> AI menulis soal teka-teki + gelar absurd -> AI menguji jawabannya -> suara narator -> video 60-90 detik
memakai template merahmu -> dikirim ke Telegram dengan tombol SETUJU / BUAT ULANG / BUANG / REVISI CAPTION.
Upload ke TikTok/Reels tetap manual.

- `config/pengaturan.json`: jumlah soal, hitung mundur, durasi, suara narator, musik.
- `config/branding.json` + `assets/branding/`: logo dan watermark (lihat BACA-SAYA.txt).
- `assets/template/template.png`: desain merahmu (jangan diganti nama). Kalau desain diganti, bilang ke aku supaya latarnya diproses ulang.
- `cloudflare/worker.js`: penerima tombol Telegram (gratis, seketika).
- Uji tampilan tanpa kuota: `python -m src.demo`.
