import { loadFont } from "@remotion/google-fonts/Fredoka";

const { fontFamily } = loadFont("normal", {
  weights: ["600", "700"],
  subsets: ["latin"],
});

// Dua palet gelap. Dipilih lewat field "tema" di JSON (bawaan: gelap).
const palet = {
  // hitam kebiruan + kuning amber + tosca
  gelap: {
    bg1: "#07090F", bg2: "#141A2E", accent: "#FFC857", accent2: "#5EEAD4",
    text: "#F8FAFC", merah: "#FF6B7A", hijau: "#4ADE80",
  },
  // ungu sangat gelap + pink + cyan
  neon: {
    bg1: "#0B0720", bg2: "#2B0F5E", accent: "#FF4FA3", accent2: "#22D3EE",
    text: "#F8F4FF", merah: "#FF6B7A", hijau: "#4ADE80",
  },
};

export const theme = {
  font: fontFamily,
  ...palet.gelap,
  // Area aman Reels/Shorts: UI platform menutup bagian bawah & kanan.
  safe: { top: 160, bottom: 520, side: 70 },
};

// Dipanggil di awal MainVideo supaya seluruh komponen memakai palet yang dipilih.
export const terapkanTema = (nama?: string): void => {
  const dipilih = nama && nama in palet ? (nama as keyof typeof palet) : "gelap";
  Object.assign(theme, palet[dipilih]);
};
