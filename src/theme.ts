import { loadFont } from "@remotion/google-fonts/Fredoka";

const { fontFamily } = loadFont("normal", {
  weights: ["600", "700"],
  subsets: ["latin"],
});

export const theme = {
  font: fontFamily,
  bg1: "#0F1B4C", // navy dalam
  bg2: "#1E2F8F", // biru kobalt
  accent: "#FFD23F", // kuning
  accent2: "#3EC1FF", // cyan
  text: "#F7F9FF",
  // Area aman Reels/Shorts: UI platform menutup bagian bawah & kanan.
  // Bawah dibuat lebih besar karena subtitle duduk di atas zona UI.
  safe: { top: 160, bottom: 470, side: 70 },
};
