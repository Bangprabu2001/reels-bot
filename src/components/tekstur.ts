// Tekstur dan bentuk kecil yang dipakai beberapa gaya (noise kertas/film, tepi sobekan).

// Noise sebagai gambar SVG (feTurbulence). rgb = "r g b" bernilai 0..1, alfa = kekuatan.
export const noiseUri = (seed: number, frek: number, alfa: number, rgb = "0 0 0"): string => {
  const [r, g, b] = rgb.split(" ");
  const svg =
    `<svg xmlns='http://www.w3.org/2000/svg' width='320' height='320'>` +
    `<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='${frek}' numOctaves='2' seed='${seed}' stitchTiles='stitch'/>` +
    `<feColorMatrix values='0 0 0 0 ${r} 0 0 0 0 ${g} 0 0 0 0 ${b} 0 0 0 ${alfa} 0'/></filter>` +
    `<rect width='100%' height='100%' filter='url(#n)'/></svg>`;
  return `url("data:image/svg+xml;utf8,${encodeURIComponent(svg)}")`;
};

// Angka acak yang selalu sama untuk masukan yang sama (supaya render konsisten).
export const acak = (n: number): number => {
  const x = Math.sin(n * 12.9898) * 43758.5453;
  return x - Math.floor(x);
};

// Tepi bergerigi yang bergerak (untuk transisi sobekan). p = 0..1.
export const poligonSobek = (p: number, seed: number, arah: "x" | "y"): string => {
  const n = 14;
  const maju = p * 112 - 6;
  const pts: string[] = [];
  if (arah === "x") {
    pts.push("0% 0%");
    for (let i = 0; i <= n; i++) {
      pts.push(`${(maju + (acak(seed * 31 + i) - 0.5) * 10).toFixed(1)}% ${((i / n) * 100).toFixed(1)}%`);
    }
    pts.push("0% 100%");
  } else {
    pts.push("0% 0%");
    for (let i = 0; i <= n; i++) {
      pts.push(`${((i / n) * 100).toFixed(1)}% ${(maju + (acak(seed * 31 + i) - 0.5) * 8).toFixed(1)}%`);
    }
    pts.push("100% 0%");
  }
  return `polygon(${pts.join(",")})`;
};

// Garis tepi sobekan statis untuk strip kertas (bagian bawah strip bergerigi).
export const tepiSobekan = (seed: number, bawah: boolean): string => {
  const n = 20;
  const pts: string[] = [];
  for (let i = 0; i <= n; i++) {
    const y = 62 + acak(seed * 17 + i) * 26;
    pts.push(`${((i / n) * 100).toFixed(1)}% ${(bawah ? 100 - y : y).toFixed(1)}%`);
  }
  return bawah
    ? `polygon(0% 100%,${pts.join(",")},100% 100%)`
    : `polygon(0% 0%,${pts.join(",")},100% 0%)`;
};
