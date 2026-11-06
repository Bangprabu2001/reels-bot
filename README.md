# Pabrik Konten Universal

Kamu ketik di Telegram **"MODE 1, Gas 1 video"** (atau MODE 2 / MODE 3). Pabrik mencari topik, riset, menulis cerita,
membuat gambar + suara, menilai dirinya sendiri, lalu mengirim video ke Telegram kamu dengan tombol
**SETUJU / BUAT ULANG / BUANG / REVISI CAPTION**. Upload ke TikTok/Reels tetap manual (tidak ada auto-upload).

## Cara pasang (sekitar 20 menit, semua gratis)

### 1. Buat bot Telegram
1. Buka Telegram, cari **@BotFather**, kirim `/newbot`, ikuti pertanyaannya.
2. Simpan **token** yang diberikan (tulisan panjang berisi angka dan huruf). Jangan dibagikan ke siapa pun.

### 2. Ambil kunci Gemini
Buka Google AI Studio, pilih **Get API key**, buat kunci, simpan.

### 3. Buat repositori GitHub baru
1. Di GitHub: **New repository**, beri nama `pabrik-konten`, pilih **Public** (agar menit Actions gratis tanpa batas;
   kunci rahasiamu tetap aman karena disimpan di Secrets, bukan di file).
2. Upload semua isi folder proyek ini. Cara termudah: **Add file → Upload files**, lalu tarik semua isi folder.
3. Folder `.github` kadang tidak ikut tertarik karena tersembunyi. Cek di repo ada `.github/workflows/pabrik.yml`.
   Kalau tidak ada: **Add file → Create new file**, ketik nama `.github/workflows/pabrik.yml`, tempel isi file itu, lalu **Commit**.

### 4. Izinkan pabrik menyimpan database topik
**Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**

### 5. Isi Secrets
**Settings → Secrets and variables → Actions → New repository secret.** Buat satu per satu:

| Nama | Isi |
|---|---|
| `TELEGRAM_BOT_TOKEN` | token dari BotFather |
| `GEMINI_API_KEY` | kunci dari AI Studio |
| `TELEGRAM_CHAT_ID` | isi nanti di langkah 6 |
| `YOUTUBE_API_KEY` | (opsional) untuk filter "tolak topik yang sudah dibuat >5 video dalam 30 hari" |

### 6. Dapatkan Chat ID
1. Buka tab **Actions → Pabrik Konten → Run workflow** (biarkan kolom mode kosong).
2. Di Telegram kirim `/start` ke botmu. Dalam ±10 menit bot membalas "Chat ID kamu: ...".
   (Bisa tekan Run workflow lagi supaya lebih cepat.)
3. Simpan angka itu sebagai secret `TELEGRAM_CHAT_ID`. Sejak ini bot hanya menurut padamu.

### 7. Coba
Kirim ke bot: `MODE 1, Gas 1 video`. Satu video butuh sekitar 10-20 menit (gambar gratis dibatasi 1 gambar per 15 detik).
Bot memberi kabar tiap tahap.

Alternatif tanpa Telegram: **Actions → Pabrik Konten → Run workflow**, isi kolom mode dengan 1, 2, atau 3.

## Uji tampilan tanpa kuota
`python -m src.demo_render 1` (atau 2, 3) membuat video contoh offline untuk mengecek overlay.

## Musik latar (opsional)
Taruh file `mode1.mp3`, `mode2.mp3`, `mode3.mp3` di folder `assets/musik/`. Mode 2 pilih musik tenang (tanpa jedag-jedug).

## Isi folder
- `config/modes.json`: rule ketiga mode (sumber kebenaran Router; ubah di sini kalau rule berubah)
- `src/s1_topic_hunter.py` ... `src/s7_telegram.py`: ketujuh tahap, `src/render.py`: pembuat video, `src/factory.py`: pengendali
- `data/topics_db.json`: database topik yang sudah di-SETUJU (tidak akan diulang)

## Batasan yang perlu kamu tahu (jujur)
- **Pesan dibaca tiap ±10 menit** (tanpa server), jadi balasan tidak instan. Jadwal GitHub kadang telat.
- **Konsistensi wajah karakter** dari gambar AI gratis tidak sempurna. Kalau wajah berubah, tekan BUAT ULANG.
- **MODE 2:** dalil Arab diambil dari riset AI. **Wajib cek ke kitab/sumber asli sebelum upload.**
- **Pasaran topik:** pengecekan "lebih dari 5 video dalam 30 hari" hanya jalan lewat YouTube (kunci opsional). TikTok/Reels/Facebook tidak bisa dibaca gratis.
- **Split screen MODE 1** tampil di babak 2-3 (sekitar 53% durasi), karena babak 1 dan 4 wajib full screen sesuai aturanmu.
- Repo Public: database topik terlihat orang lain. Repo Private boleh, tapi ganti jadwal `*/10` jadi `*/30` di `pabrik.yml` agar jatah menit gratis tidak habis.
- Kalau tidak ada aktivitas di repo 60 hari, GitHub mematikan jadwal otomatis. Tekan Run workflow sekali untuk menyalakan lagi.
