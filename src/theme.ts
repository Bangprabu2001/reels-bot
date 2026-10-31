import { loadFont as muatSpace } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as muatMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as muatCaveat } from "@remotion/google-fonts/Caveat";
import { loadFont as muatLora } from "@remotion/google-fonts/Lora";
import { loadFont as muatPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as muatNunito } from "@remotion/google-fonts/Nunito";

const space = muatSpace("normal", { weights: ["700"], subsets: ["latin"] }).fontFamily;
const mono = muatMono("normal", { weights: ["700"], subsets: ["latin"] }).fontFamily;
const caveat = muatCaveat("normal", { weights: ["700"], subsets: ["latin"] }).fontFamily;
const lora = muatLora("normal", { weights: ["400", "700"], subsets: ["latin"] }).fontFamily;
const playfair = muatPlayfair("normal", { weights: ["700", "900"], subsets: ["latin"] }).fontFamily;
const nunito = muatNunito("normal", { weights: ["700", "800"], subsets: ["latin"] }).fontFamily;

export type KodeGaya =
  | "STYLE_HUD_TECH"
  | "STYLE_PAPER_DAKWAH"
  | "STYLE_RETRO_NOIR"
  | "STYLE_CLAY_3D";

export type Gaya = {
  kode: KodeGaya;
  terang: boolean; // latar terang (kertas, clay) atau gelap
  bg1: string;
  bg2: string;
  text: string;
  accent: string;
  accent2: string;
  merah: string;
  hijau: string;
  kartu: string; // isi kartu/panel
  kartuTepi: string;
  trek: string; // jalur batang grafik
  bar2: string; // warna kedua batang grafik
  teksTepi: string; // tepi huruf agar terbaca di atas gambar
  teksBayang: string;
  teksDiAksen: string; // warna huruf di atas warna aksen
  garis: string; // warna garis/bingkai
  font: string; // judul
  fontBody: string; // isi scene data
  fontSub: string; // subtitle
  caps: boolean;
  tracking: number;
  teksGaya: number; // 0 pop, 1 geser, 2 ketik
  popAwal: number; // skala awal saat teks muncul
  subTeks: string;
  subAktif: string;
  subTepi: string;
  subTepiLebar: number;
  subUkuran: number;
  redupRgb: string; // warna lapisan di atas ilustrasi scene data
  masuk: string[]; // jenis transisi masuk yang bergantian
  sfxPeta: Record<string, string>; // nama efek logis -> efek yang dipakai gaya ini
};

// Empat gaya. Satu video memakai SATU gaya saja; tidak boleh dicampur.
const GAYA: Record<KodeGaya, Gaya> = {
  // 1. Neon HUD Line Motion: hitam, garis tipis putih, cyan, target merah
  STYLE_HUD_TECH: {
    kode: "STYLE_HUD_TECH", terang: false,
    bg1: "#000000", bg2: "#0A0A0A", text: "#FFFFFF", accent: "#00F0FF", accent2: "#FF3B30",
    merah: "#FF3B30", hijau: "#00F0FF",
    kartu: "rgba(255,255,255,0.04)", kartuTepi: "rgba(255,255,255,0.85)", trek: "rgba(255,255,255,0.12)", bar2: "#FFFFFF",
    teksTepi: "#000000", teksBayang: "0 0 18px rgba(0,240,255,0.55)", teksDiAksen: "#000000", garis: "#FFFFFF",
    font: space, fontBody: mono, fontSub: mono, caps: true, tracking: 4, teksGaya: 2, popAwal: 0.6,
    subTeks: "#FFFFFF", subAktif: "#00F0FF", subTepi: "#000000", subTepiLebar: 6, subUkuran: 66,
    redupRgb: "0,0,0", masuk: ["glitch", "scan", "data"],
    sfxPeta: { pop: "tick", whoosh: "whoosh", ding: "ding" },
  },
  // 2. Paper-cut Stickman Scrapbook: krem, pastel, tulisan tangan
  STYLE_PAPER_DAKWAH: {
    kode: "STYLE_PAPER_DAKWAH", terang: true,
    bg1: "#F5F1E8", bg2: "#EFE8D8", text: "#1A1A1A", accent: "#C67C5A", accent2: "#8AA8B5",
    merah: "#C67C5A", hijau: "#A8B5A2",
    kartu: "rgba(255,253,247,0.9)", kartuTepi: "#1A1A1A", trek: "rgba(26,26,26,0.12)", bar2: "#8AA8B5",
    teksTepi: "#F5F1E8", teksBayang: "0 4px 10px rgba(0,0,0,0.18)", teksDiAksen: "#FFFFFF", garis: "#1A1A1A",
    font: caveat, fontBody: lora, fontSub: caveat, caps: false, tracking: 0, teksGaya: 0, popAwal: 0.8,
    subTeks: "#1A1A1A", subAktif: "#C67C5A", subTepi: "#F5F1E8", subTepiLebar: 12, subUkuran: 92,
    redupRgb: "245,241,232", masuk: ["sobek", "tempel"],
    sfxPeta: { pop: "rustle", whoosh: "rustle", ding: "ding" },
  },
  // 3. Grainy Retro Noir Halftone: koran tua, hitam putih, satu aksen merah
  STYLE_RETRO_NOIR: {
    kode: "STYLE_RETRO_NOIR", terang: false,
    bg1: "#E8E0D0", bg2: "#D8CFBC", text: "#FFFFFF", accent: "#C41E1E", accent2: "#FFFFFF",
    merah: "#C41E1E", hijau: "#FFFFFF",
    kartu: "rgba(0,0,0,0.62)", kartuTepi: "#FFFFFF", trek: "rgba(255,255,255,0.18)", bar2: "#FFFFFF",
    teksTepi: "#000000", teksBayang: "0 6px 0 rgba(0,0,0,0.7)", teksDiAksen: "#FFFFFF", garis: "#000000",
    font: playfair, fontBody: playfair, fontSub: playfair, caps: false, tracking: 0, teksGaya: 2, popAwal: 0.6,
    subTeks: "#FFFFFF", subAktif: "#E8453C", subTepi: "#000000", subTepiLebar: 9, subUkuran: 78,
    redupRgb: "0,0,0", masuk: ["tinta", "robek", "potong"],
    sfxPeta: { pop: "ketik", whoosh: "whoosh", ding: "ding" },
  },
  // 4. Soft Clay 3D Isometric: pastel bersih, bulat, memantul
  STYLE_CLAY_3D: {
    kode: "STYLE_CLAY_3D", terang: true,
    bg1: "#E9E6FF", bg2: "#D6F0E0", text: "#2B2B3A", accent: "#FF7A59", accent2: "#6C7BFF",
    merah: "#FF6B6B", hijau: "#3DC98A",
    kartu: "rgba(255,255,255,0.92)", kartuTepi: "rgba(43,43,58,0.15)", trek: "rgba(43,43,58,0.1)", bar2: "#6C7BFF",
    teksTepi: "#FFFFFF", teksBayang: "0 6px 14px rgba(60,40,120,0.25)", teksDiAksen: "#FFFFFF", garis: "#2B2B3A",
    font: nunito, fontBody: nunito, fontSub: nunito, caps: false, tracking: 0, teksGaya: 0, popAwal: 0.5,
    subTeks: "#2B2B3A", subAktif: "#FF7A59", subTepi: "#FFFFFF", subTepiLebar: 12, subUkuran: 82,
    redupRgb: "255,255,255", masuk: ["pop"],
    sfxPeta: { pop: "pop", whoosh: "whoosh", ding: "ding" },
  },
};

export const theme: Gaya & { safe: { top: number; bottom: number; side: number } } = {
  ...GAYA.STYLE_HUD_TECH,
  // Area aman Reels/Shorts: UI platform menutup bagian bawah & kanan.
  safe: { top: 160, bottom: 520, side: 70 },
};

// Dipanggil di awal MainVideo supaya seluruh komponen memakai gaya yang dipilih.
export const terapkanGaya = (kode?: string, latar?: string): void => {
  const g = kode && kode in GAYA ? GAYA[kode as KodeGaya] : GAYA.STYLE_HUD_TECH;
  Object.assign(theme, g);
  if (g.kode === "STYLE_CLAY_3D" && latar && /^#[0-9a-fA-F]{6}$/.test(latar)) theme.bg1 = latar;
};
