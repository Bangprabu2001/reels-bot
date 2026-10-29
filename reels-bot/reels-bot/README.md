# reels-bot (versi gratis, agentik)

topik -> [Agen Naskah] -> [Agen Pemeriksa Fakta] -> [Agen Suara + Subtitle] -> Remotion render -> video 9:16
Upload ke platform dilakukan manual.

## Siapkan sekali
1. Ambil API key gratis di Google AI Studio.
2. Install dependensi lokal:
   ```bash
   npm i --save-exact remotion @remotion/cli @remotion/google-fonts react react-dom
   npm i -D typescript @types/react @types/react-dom
   pip install -r scripts/requirements.txt
   ```
3. `export GEMINI_API_KEY=...` (Windows PowerShell: `$env:GEMINI_API_KEY="..."`)

## Jalankan di laptop
```bash
python3 scripts/pipeline.py "topik kamu"   # naskah + suara -> data/latest.json
npm run studio                              # preview
npm run render                              # hasil: out/video.mp4
```
Kalau laptop berat, render lewat GitHub Actions (di bawah).

## Render di cloud (laptop tidak terbebani)
1. Buat repo GitHub, push seluruh folder ini (termasuk `package.json` dan `package-lock.json` setelah npm install).
2. Settings -> Secrets and variables -> Actions -> tambah secret `GEMINI_API_KEY`.
3. Tab Actions -> "Buat dan render video" -> Run workflow (isi topik atau kosongkan untuk ambil dari `topik.txt`).
4. Setelah selesai, unduh artifact `video-siap-upload`, tonton, lalu upload sendiri.
Jadwal harian: hapus tanda `#` pada bagian `schedule` di `.github/workflows/render.yml`.

## Catatan
- Nama model Gemini bisa diganti: `GEMINI_MODEL=...`. Batas gratis dan nama model bisa berubah, cek di AI Studio.
- Suara: `VOICE=id-ID-GadisNeural` untuk suara perempuan.
- Pemeriksa fakta mencetak "Cek manual" di terminal; selalu baca sebelum upload.
- Musik latar: taruh file di `public/` dan tambah `"musikSrc": "musik.mp3"` di JSON.
- Contoh tanpa suara: `npm run render:contoh`.
