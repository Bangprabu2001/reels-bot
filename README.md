# Pabrik Konten Universal

Semua lewat tombol di Telegram. Tekan **🏭 MENU** lalu pilih MODE 1 / 2 / 3. Pabrik mencari topik, riset, menulis cerita,
membuat gambar + suara, menilai dirinya sendiri, lalu mengirim video dengan tombol **SETUJU / BUAT ULANG / BUANG / REVISI CAPTION**.
Upload ke TikTok/Reels tetap manual.

## Cara kerja
- **Cloudflare Worker** (`cloudflare/worker.js`, gratis): menjawab tombol seketika, lalu menyalakan GitHub Actions hanya saat ada pekerjaan berat.
- **GitHub Actions** (`.github/workflows/pabrik.yml`): membuat video (±8-15 menit).
- **Gemini** (otak, pindah model otomatis kalau kuota habis), **Pollinations** (gambar), **edge-tts** (suara), **ffmpeg** (video).

## Pasang
Ikuti panduan lengkap di chat, urutannya: Bot Telegram -> kunci Gemini -> repo GitHub -> Secrets -> token GitHub -> Cloudflare Worker -> sambungkan webhook -> tes.

Secrets di GitHub (Settings -> Secrets and variables -> Actions): `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, (opsional) `YOUTUBE_API_KEY`, `POLLINATIONS_TOKEN`.
Variabel di Cloudflare: `TELEGRAM_BOT_TOKEN`, `GITHUB_TOKEN`, `WEBHOOK_SECRET`, `GITHUB_REPO`, `OWNER_CHAT_ID`, (opsional) `GITHUB_BRANCH`.

## Uji tampilan tanpa kuota
`python -m src.demo_render 1` (atau 2, 3).

## Musik latar (opsional)
`assets/musik/mode1.mp3`, `mode2.mp3`, `mode3.mp3`.

## Batasan jujur
- Gambar AI gratis: wajah karakter tidak selalu konsisten. Tekan BUAT ULANG.
- MODE 2: dalil Arab berasal dari riset AI, wajib cek ke kitab asli sebelum upload.
- Cek "topik pasaran" hanya lewat YouTube (kunci opsional). TikTok/Reels/Facebook tidak bisa dibaca gratis.
- Split screen MODE 1 tampil di babak 2-3 (±53% durasi), karena babak 1 dan 4 wajib full screen.
- Kuota gratis Gemini terbatas; kalau semua model habis, tunggu reset harian (sekitar 14.00-15.00 WIB).
