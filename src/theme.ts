import { loadFont } from "@remotion/google-fonts/Fredoka";

const { fontFamily } = loadFont("normal", {
  weights: ["600", "700"],
  subsets: ["latin"],
});

// Lima palet warna. Dipilih lewat field "tema" di JSON (menu "tema" saat Run workflow).
const palet = {
  // navy + kuning (tampilan awal)
  klasik: {
    bg1: "#0F1B4C", bg2: "#1E2F8F", accent: "#FFD23F", accent2: "#3EC1FF",
    text: "#F7F9FF", merah: "#FF5C6C", hijau: "#3DDC97",
    karakterUtama: "#FFD23F", karakterAksen: "#3EC1FF", karakterCahaya: "#3EC1FF",
  },
  // ungu gelap + pink + cyan, kesan neon/gaming
  neon: {
    bg1: "#0B0720", bg2: "#2B0F5E", accent: "#FF3D9A", accent2: "#00E5FF",
    text: "#F8F4FF", merah: "#FF5C6C", hijau: "#3DDC97",
    karakterUtama: "#B6FF3B", karakterAksen: "#FF3D9A", karakterCahaya: "#00E5FF",
  },
  // ungu plum + oranye hangat, kesan senja
  sunset: {
    bg1: "#2B0F3A", bg2: "#8A1F5C", accent: "#FFB347", accent2: "#FF6B8B",
    text: "#FFF6EC", merah: "#FF5C6C", hijau: "#3DDC97",
    karakterUtama: "#FFD166", karakterAksen: "#EF476F", karakterCahaya: "#FFC857",
  },
  // hijau tosca tua + emas, kesan alam/tenang
  hutan: {
    bg1: "#062B2B", bg2: "#0F5C4D", accent: "#F9D65C", accent2: "#7CF5C8",
    text: "#F4FFF8", merah: "#FF6B6B", hijau: "#3DDC97",
    karakterUtama: "#7CF5C8", karakterAksen: "#F9D65C", karakterCahaya: "#F9D65C",
  },
  // hitam + kuning terang, kontras tinggi dan tegas
  kontras: {
    bg1: "#0A0A0A", bg2: "#232323", accent: "#FFE600", accent2: "#00E0FF",
    text: "#FFFFFF", merah: "#FF3B30", hijau: "#3DDC97",
    karakterUtama: "#FFE600", karakterAksen: "#FF3B30", karakterCahaya: "#00E0FF",
  },
};

export const theme = {
  font: fontFamily,
  ...palet.klasik,
  // Area aman Reels/Shorts: UI platform menutup bagian bawah & kanan.
  // Bawah diberi ruang untuk baris karakter + subtitle di atas zona UI.
  safe: { top: 160, bottom: 600, side: 70 },
};

// Dipanggil di awal MainVideo supaya seluruh komponen memakai palet yang dipilih.
export const terapkanTema = (nama?: string): void => {
  const dipilih = nama && nama in palet ? (nama as keyof typeof palet) : "klasik";
  Object.assign(theme, palet[dipilih]);
};
