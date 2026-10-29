# reels-bot (versi gratis, agentik)

topik -> [Agen Naskah] -> [Agen Pemeriksa Fakta] -> [Agen Suara + Subtitle] -> [Agen B-roll] -> Remotion render -> video 9:16
Upload ke platform dilakukan manual.

## Fitur tampilan
- 7 template scene: hook, bar_chart, list, big_number, compare, timeline, outro
- Maskot "Mimo": mulut bergerak mengikuti suara, berkedip, ekspresi senang/kaget/mikir
- Subtitle animasi per kata
- Video latar (b-roll) gratis dari Pixabay atau Pexels (opsional)
- Durasi target bebas: 45-180 detik (atau lebih)
- Musik latar: taruh file `musik.mp3` di folder `public/` (otomatis dipakai, volume kecil)

## Render di cloud (laptop tidak terbebani)
1. Unggah isi folder ini ke repo GitHub (timpa file lama).
2. Settings -> Secrets and variables -> Actions -> New repository secret:
   - `GEMINI_API_KEY` (wajib, dari Google AI Studio)
   - `PIXABAY_API_KEY` (opsional, untuk b-roll; kunci ada di pixabay.com/api/docs setelah login)
   - atau `PEXELS_API_KEY` (alternatif, dari pexels.com/api)
3. Tab Actions -> "Buat dan render video" -> Run workflow: isi topik, pilih durasi.
4. Unduh artifact `video-siap-upload`, tonton, cek "Cek manual" di log, lalu upload sendiri.

## Di laptop (opsional)
```bash
npm i --save-exact remotion @remotion/cli @remotion/google-fonts react react-dom
npm i -D typescript @types/react @types/react-dom
pip install -r scripts/requirements.txt
python3 scripts/pipeline.py "topik kamu" 90
npm run studio      # preview
npm run render      # out/video.mp4
```
`npm run render:contoh` merender contoh bawaan (data/example.json) tanpa suara.

## Catatan
- Model Gemini utama bisa diganti: `GEMINI_MODEL=...` (ada model cadangan otomatis).
- Suara: `VOICE=id-ID-GadisNeural` untuk suara perempuan.
- Pemeriksa fakta mencetak "Cek manual" di log; selalu baca sebelum upload.
- Video Pixabay/Pexels boleh dipakai gratis; mencantumkan kredit tidak wajib (log mencetak daftar kreditnya). Pixabay kebanyakan video landscape, jadi di layar vertikal bagian tengahnya yang dipotong.
- Tambah template baru: komponen di `src/scenes/`, tipe di `src/types.ts`, daftar di `src/scenes/index.tsx`, dan skema di `scripts/pipeline.py`.
