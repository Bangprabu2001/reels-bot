# reels-bot: video edukasi gaya cerita bergambar

topik -> [Agen Naskah] -> [Agen Pemeriksa Fakta] -> [Agen Suara + Subtitle] -> [Agen Ilustrator] -> Remotion render -> video 9:16
Upload ke platform dilakukan manual.

## Tampilan
- Tema gelap. Tiap scene punya ilustrasi kartun gaya buku cerita (dibuat AI, gratis lewat Pollinations)
  dengan gerak kamera pelan dan partikel bercahaya. Tidak ada karakter maskot yang melayang; ilustrasi boleh berisi manusia, hewan, benda, atau tempat. Subtitle di tengah layar tanpa panel (huruf bertepi tebal) agar gambar tetap terlihat.
- 10 template scene: hook, cerita (ilustrasi penuh + subtitle di tengah), fakta, mitos_fakta, big_number, bar_chart, compare, timeline, list, outro.
- Efek suara dibuat lewat kode (whoosh, pop, ding). Bisa diganti dengan file sendiri di `public/sfx/` (mp3).
- Musik latar: taruh `musik.mp3` di folder `public/`.

## Render di cloud
1. Unggah isi folder ini ke repo GitHub.
2. Secrets: `GEMINI_API_KEY` (wajib). Opsional: `POLLINATIONS_API_KEY` (daftar gratis di enter.pollinations.ai)
   supaya gambar lebih cepat dan tanpa watermark.
3. Actions -> "Buat dan render video" -> Run workflow (topik + durasi).
4. Unduh artifact `video-siap-upload`, cek "Cek manual" di log, upload sendiri.

## Suara
- Narator memakai Gemini TTS (Google AI Studio) dengan kunci GEMINI_API_KEY yang sama. Nama suara diisi di kolom `suara` saat Run workflow.
- Kalau Gemini TTS gagal atau jatahnya habis, otomatis memakai suara cadangan edge-tts.
- Bahan unggah (judul, deskripsi, hashtag) ada di artifact `info-unggah.txt`.

## Catatan
- Tanpa kunci Pollinations, gambar dibuat sekitar satu per 15 detik, jadi proses lebih lama (beberapa menit).
- Kalau sebuah ilustrasi gagal dibuat, scene itu memakai latar polos bergerak; video tetap jadi.
- Video stok (Pixabay/Pexels) masih ada sebagai opsi lama: set env `BROLL=ya` (butuh kunci masing-masing).
- `GEMINI_MODEL`, `VOICE`, `KECEPATAN`, `MAKS_GAMBAR` bisa diatur lewat env.
