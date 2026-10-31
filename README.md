# reels-bot: video edukasi dengan 4 gaya (satu gaya per video, tidak dicampur)

topik -> [Agen Naskah + pemilih gaya] -> [Pemeriksa Fakta] -> [Suara + Subtitle] -> [Ilustrator] -> Remotion render -> video 9:16
Upload ke platform dilakukan manual.

## Empat gaya
| Kode | Untuk topik | Tampilan | Suara | Musik (taruh di `public/`) |
|---|---|---|---|---|
| STYLE_HUD_TECH | Sains, otak, tidur, psikologi, teknologi, medis, self-improvement, data | Hitam + titik halus, garis putih tipis, cyan, kotak target merah, label data, pewaktu, gelombang, garis pindai; transisi glitch/scan/data wipe | Charon (dalam, tenang) | `musik_hud.mp3` |
| STYLE_PAPER_DAKWAH | Dakwah, parenting Qurani, adab, akhlak, keluarga, nasehat, anak islami | Kertas krem bertekstur, sobekan, selotip, foto tempel, tulisan tangan (Caveat/Lora), pastel; transisi sobekan/ditempel | Sulafat (hangat) | `musik_paper.mp3` |
| STYLE_RETRO_NOIR | Sejarah Islam, sirah, konspirasi, true story, perang, misteri | Koran tua, foto fotokopi hitam putih + halftone, butiran film, goresan, kedip, satu aksen merah, Playfair Display; transisi tinta/robekan/potong | Algenib (rendah, dramatis) | `musik_noir.mp3` |
| STYLE_CLAY_3D | Keuangan, bisnis, produktivitas, habit, edukasi modern, fintech | Pastel bersih, gelembung lembut, kartu empuk memantul, Nunito; transisi pop | Puck (ceria) | `musik_clay.mp3` |

Gaya dipilih otomatis dari topik, atau dipaksa lewat menu `gaya` saat Run workflow. Musik: kalau ada `musik_<gaya>.mp3` itu yang dipakai, kalau tidak `musik.mp3`.

## Render di cloud
1. Unggah isi folder ini ke repo GitHub.
2. Secrets: `GEMINI_API_KEY` (wajib). Opsional: `POLLINATIONS_API_KEY` (gambar lebih cepat, tanpa watermark).
3. Actions -> "Buat dan render video" -> Run workflow (topik, durasi, gaya, suara).
4. Unduh artifact `video-siap-upload`; cek "Cek manual" di log; bahan unggah ada di `info-unggah.txt`.

## Catatan
- Template gambar diadaptasi dari rancangan gaya: bendera `--style/--no` diganti kalimat "Avoid"; label teks HUD dibuat lewat kode (AI gambar sering menghasilkan huruf acak).
- Label HUD bersifat dekoratif; angka statistik tidak boleh dikarang.
- Gaya islami (Paper, Noir): dilarang menggambarkan Nabi, Rasul, sahabat, malaikat, atau sosok suci.
- Efek suara dibuat lewat kode: tick (HUD), gemerisik (Kertas), ketikan mesin tik (Noir), pop (Clay), whoosh, ding. Bisa diganti file sendiri di `public/sfx/` (mp3).
- Tanpa kunci Pollinations, gambar dibuat sekitar satu per 15 detik (proses lebih lama).
