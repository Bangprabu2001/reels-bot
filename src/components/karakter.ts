// Gambar karakter sebagai teks SVG murni (tanpa React), supaya mudah diuji dan diganti.
// Tiga karakter: "mimo" (makhluk bulat), "bolt" (robot), "miko" (kucing).

export type Ekspresi = "senang" | "kaget" | "mikir";

export type ParamKarakter = {
  bicara: number; // 0..1: seberapa lebar mulut terbuka
  kedip: number; // 0.1..1: seberapa terbuka mata
  ekspresi: Ekspresi;
  lambai: number; // derajat: seberapa terangkat lengan kanan
  fase: number; // untuk gerak batang suara pada robot
  utama: string; // warna badan (#rrggbb)
  aksen: string; // warna pelengkap (#rrggbb)
  cahaya: string; // warna cahaya layar robot (#rrggbb)
};

const GELAP = "#1B1F3B";
const MULUT = "#5A1020";
const LIDAH = "#FF7A8A";
const PIPI = "#FF8FA3";

const f = (n: number): string => n.toFixed(1);

const campur = (hex: string, ke: number, t: number): string => {
  const h = hex.replace("#", "");
  const c = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  const o = c.map((v) => Math.round(v + (ke - v) * t).toString(16).padStart(2, "0"));
  return "#" + o.join("");
};

const bungkus = (isi: string, defs: string): string =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%"><defs>${defs}</defs>${isi}</svg>`;

const gradien = (utama: string): string =>
  `<radialGradient id="gb" cx="35%" cy="30%" r="85%"><stop offset="0" stop-color="${campur(utama, 255, 0.4)}"/><stop offset="1" stop-color="${campur(utama, 0, 0.08)}"/></radialGradient>`;

const garis = `stroke="${GELAP}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"`;

// ---------- bagian yang dipakai bersama ----------

const mata = (cx: number, cy: number, p: ParamKarakter): string => {
  const kaget = p.ekspresi === "kaget";
  const mikir = p.ekspresi === "mikir";
  const rx = kaget ? 17 : 15;
  const ry = (kaget ? 21 : 17) * p.kedip;
  const px = mikir ? 4 : 0;
  const py = mikir ? -5 : 0;
  const pr = kaget ? 6 : 8.5;
  return (
    `<ellipse cx="${f(cx)}" cy="${f(cy)}" rx="${rx}" ry="${f(ry)}" fill="#ffffff" stroke="${GELAP}" stroke-width="4"/>` +
    `<ellipse cx="${f(cx + px)}" cy="${f(cy + py)}" rx="${pr}" ry="${f(pr * 1.15 * p.kedip)}" fill="${GELAP}"/>` +
    `<circle cx="${f(cx + px + 3)}" cy="${f(cy + py - 3.5 * p.kedip)}" r="${f(3 * p.kedip)}" fill="#ffffff"/>`
  );
};

const alis = (x1: number, x2: number, y: number, p: ParamKarakter, warna = GELAP): string => {
  const g = `stroke="${warna}" stroke-width="5" fill="none" stroke-linecap="round"`;
  if (p.ekspresi === "kaget") {
    return (
      `<path d="M${x1 - 16} ${y - 4} Q${x1} ${y - 17} ${x1 + 16} ${y - 4}" ${g}/>` +
      `<path d="M${x2 - 16} ${y - 4} Q${x2} ${y - 17} ${x2 + 16} ${y - 4}" ${g}/>`
    );
  }
  if (p.ekspresi === "mikir") {
    return (
      `<path d="M${x1 - 14} ${y + 2} Q${x1} ${y} ${x1 + 14} ${y + 4}" ${g}/>` +
      `<path d="M${x2 - 14} ${y - 8} Q${x2} ${y - 20} ${x2 + 14} ${y - 10}" ${g}/>`
    );
  }
  return "";
};

const mulutTerbuka = (cx: number, cy: number, p: ParamKarakter): string => {
  if (p.ekspresi === "kaget") {
    return `<ellipse cx="${f(cx)}" cy="${f(cy + 6)}" rx="10" ry="15" fill="${MULUT}" stroke="${GELAP}" stroke-width="4"/>`;
  }
  if (p.bicara > 0.05) {
    const ry = 3 + 17 * p.bicara;
    const my = cy + ry * 0.2;
    return (
      `<ellipse cx="${f(cx)}" cy="${f(my)}" rx="14" ry="${f(ry)}" fill="${MULUT}" stroke="${GELAP}" stroke-width="4"/>` +
      (ry > 11
        ? `<ellipse cx="${f(cx)}" cy="${f(my + ry * 0.5)}" rx="8" ry="${f(ry * 0.4)}" fill="${LIDAH}"/>`
        : "")
    );
  }
  if (p.ekspresi === "mikir") {
    return `<path d="M${cx - 12} ${cy + 2} Q${cx} ${cy - 2} ${cx + 14} ${cy + 4}" ${garis}/>`;
  }
  return `<path d="M${cx - 20} ${cy - 2} Q${cx} ${cy + 16} ${cx + 20} ${cy - 2}" ${garis}/>`;
};

const kilap = (cx: number, cy: number, rx: number, ry: number, sudut: number): string =>
  `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#ffffff" opacity="0.38" transform="rotate(${sudut} ${cx} ${cy})"/>`;

// ---------- Mimo: makhluk bulat dengan tunas ----------

const mimo = (p: ParamKarakter): string => {
  const isi =
    `<ellipse cx="100" cy="190" rx="52" ry="7" fill="#000000" opacity="0.25"/>` +
    // tunas
    `<path d="M100 46 Q97 24 114 14" stroke="${GELAP}" stroke-width="12" fill="none" stroke-linecap="round"/>` +
    `<path d="M100 46 Q97 24 114 14" stroke="${p.aksen}" stroke-width="6" fill="none" stroke-linecap="round"/>` +
    `<path d="M114 14 Q136 4 142 26 Q118 34 114 14 Z" fill="${p.aksen}" stroke="${GELAP}" stroke-width="4" stroke-linejoin="round"/>` +
    // lengan (di belakang badan)
    `<g transform="rotate(${f(8 - p.lambai * 0.3)} 32 124)"><ellipse cx="22" cy="138" rx="13" ry="23" fill="${p.utama}" stroke="${GELAP}" stroke-width="5"/></g>` +
    `<g transform="rotate(${f(-p.lambai)} 168 124)"><ellipse cx="178" cy="138" rx="13" ry="23" fill="${p.utama}" stroke="${GELAP}" stroke-width="5"/></g>` +
    // kaki
    `<ellipse cx="70" cy="182" rx="22" ry="11" fill="${p.aksen}" stroke="${GELAP}" stroke-width="5"/>` +
    `<ellipse cx="130" cy="182" rx="22" ry="11" fill="${p.aksen}" stroke="${GELAP}" stroke-width="5"/>` +
    // badan
    `<ellipse cx="100" cy="116" rx="72" ry="68" fill="url(#gb)" stroke="${GELAP}" stroke-width="6"/>` +
    kilap(70, 72, 22, 11, -30) +
    `<circle cx="50" cy="130" r="11" fill="${PIPI}" opacity="0.65"/>` +
    `<circle cx="150" cy="130" r="11" fill="${PIPI}" opacity="0.65"/>` +
    mata(72, 106, p) +
    mata(128, 106, p) +
    alis(72, 128, 80, p) +
    mulutTerbuka(100, 140, p);
  return bungkus(isi, gradien(p.utama));
};

// ---------- Bolt: robot ----------

const mataRobot = (cx: number, cy: number, p: ParamKarakter): string => {
  const kaget = p.ekspresi === "kaget";
  const rx = kaget ? 14 : 12;
  const ry = (kaget ? 18 : 14) * p.kedip;
  return (
    `<ellipse cx="${f(cx)}" cy="${f(cy)}" rx="${rx + 5}" ry="${f(ry + 5)}" fill="${p.cahaya}" opacity="0.28"/>` +
    `<ellipse cx="${f(cx)}" cy="${f(cy)}" rx="${rx}" ry="${f(ry)}" fill="${p.cahaya}"/>` +
    `<circle cx="${f(cx + 3)}" cy="${f(cy - 4 * p.kedip)}" r="${f(3.2 * p.kedip)}" fill="#ffffff"/>`
  );
};

const mulutRobot = (p: ParamKarakter): string => {
  const g = `stroke="${p.cahaya}" stroke-width="6" fill="none" stroke-linecap="round"`;
  if (p.ekspresi === "kaget") return `<ellipse cx="100" cy="112" rx="9" ry="11" ${g}/>`;
  if (p.bicara > 0.05) {
    let batang = "";
    for (let i = 0; i < 5; i++) {
      const h = 5 + 16 * p.bicara * (0.45 + 0.55 * Math.abs(Math.sin(p.fase * 0.9 + i * 1.7)));
      batang += `<rect x="${f(65 + i * 15)}" y="${f(113 - h / 2)}" width="9" height="${f(h)}" rx="4.5" fill="${p.cahaya}"/>`;
    }
    return batang;
  }
  if (p.ekspresi === "mikir") return `<path d="M84 114 L116 110" ${g}/>`;
  return `<path d="M80 108 Q100 124 120 108" ${g}/>`;
};

const bolt = (p: ParamKarakter): string => {
  const isi =
    `<ellipse cx="100" cy="193" rx="46" ry="6" fill="#000000" opacity="0.25"/>` +
    // antena
    `<path d="M100 36 L100 18" stroke="${GELAP}" stroke-width="6" stroke-linecap="round"/>` +
    `<circle cx="100" cy="13" r="9" fill="${p.aksen}" stroke="${GELAP}" stroke-width="4"/>` +
    // telinga
    `<rect x="12" y="78" width="20" height="40" rx="8" fill="${p.aksen}" stroke="${GELAP}" stroke-width="5"/>` +
    `<rect x="168" y="78" width="20" height="40" rx="8" fill="${p.aksen}" stroke="${GELAP}" stroke-width="5"/>` +
    // lengan
    `<g transform="rotate(${f(6 - p.lambai * 0.3)} 56 160)"><rect x="34" y="158" width="20" height="30" rx="10" fill="${p.utama}" stroke="${GELAP}" stroke-width="5"/></g>` +
    `<g transform="rotate(${f(-p.lambai)} 144 160)"><rect x="146" y="158" width="20" height="30" rx="10" fill="${p.utama}" stroke="${GELAP}" stroke-width="5"/></g>` +
    // badan
    `<rect x="60" y="146" width="80" height="42" rx="18" fill="url(#gb)" stroke="${GELAP}" stroke-width="5"/>` +
    `<circle cx="100" cy="167" r="8" fill="${p.aksen}" stroke="${GELAP}" stroke-width="3"/>` +
    // kepala
    `<rect x="26" y="34" width="148" height="116" rx="40" fill="url(#gb)" stroke="${GELAP}" stroke-width="6"/>` +
    kilap(62, 50, 20, 7, -20) +
    // layar wajah
    `<rect x="44" y="52" width="112" height="76" rx="28" fill="#0E1330" stroke="${GELAP}" stroke-width="4"/>` +
    mataRobot(76, 84, p) +
    mataRobot(124, 84, p) +
    alis(76, 124, 62, p, p.cahaya) +
    mulutRobot(p);
  return bungkus(isi, gradien(p.utama));
};

// ---------- Miko: kucing ----------

const mikoMulut = (p: ParamKarakter): string => {
  if (p.ekspresi === "kaget") {
    return `<ellipse cx="100" cy="128" rx="9" ry="13" fill="${MULUT}" stroke="${GELAP}" stroke-width="4"/>`;
  }
  if (p.bicara > 0.05) {
    const ry = 3 + 13 * p.bicara;
    return `<ellipse cx="100" cy="${f(122 + ry * 0.6)}" rx="11" ry="${f(ry)}" fill="${MULUT}" stroke="${GELAP}" stroke-width="4"/>`;
  }
  return `<path d="M100 112 Q100 122 89 124 M100 112 Q100 122 111 124" ${garis.replace('stroke-width="5"', 'stroke-width="4"')}/>`;
};

const miko = (p: ParamKarakter): string => {
  const isi =
    `<ellipse cx="100" cy="193" rx="50" ry="6" fill="#000000" opacity="0.25"/>` +
    // ekor (garis luar lalu isi)
    `<path d="M136 180 Q186 176 176 132" stroke="${GELAP}" stroke-width="20" fill="none" stroke-linecap="round"/>` +
    `<path d="M136 180 Q186 176 176 132" stroke="${p.utama}" stroke-width="10" fill="none" stroke-linecap="round"/>` +
    // badan (duduk)
    `<ellipse cx="100" cy="164" rx="40" ry="30" fill="url(#gb)" stroke="${GELAP}" stroke-width="5"/>` +
    // kaki depan
    `<ellipse cx="82" cy="186" rx="12" ry="8" fill="${p.utama}" stroke="${GELAP}" stroke-width="4"/>` +
    `<g transform="rotate(${f(-p.lambai)} 128 156)"><ellipse cx="130" cy="172" rx="11" ry="17" fill="${p.utama}" stroke="${GELAP}" stroke-width="4"/></g>` +
    // telinga
    `<path d="M34 70 L42 14 L88 44 Z" fill="${p.utama}" stroke="${GELAP}" stroke-width="5" stroke-linejoin="round"/>` +
    `<path d="M46 56 L50 30 L72 46 Z" fill="#FF9EB5"/>` +
    `<path d="M166 70 L158 14 L112 44 Z" fill="${p.utama}" stroke="${GELAP}" stroke-width="5" stroke-linejoin="round"/>` +
    `<path d="M154 56 L150 30 L128 46 Z" fill="#FF9EB5"/>` +
    // kepala
    `<ellipse cx="100" cy="88" rx="74" ry="56" fill="url(#gb)" stroke="${GELAP}" stroke-width="6"/>` +
    kilap(66, 56, 20, 9, -28) +
    // garis dahi
    `<path d="M100 36 L100 54" stroke="${p.aksen}" stroke-width="6" stroke-linecap="round"/>` +
    `<path d="M84 38 L88 54" stroke="${p.aksen}" stroke-width="6" stroke-linecap="round"/>` +
    `<path d="M116 38 L112 54" stroke="${p.aksen}" stroke-width="6" stroke-linecap="round"/>` +
    // kumis
    `<path d="M30 98 L6 92 M30 106 L8 110 M170 98 L194 92 M170 106 L192 110" stroke="${GELAP}" stroke-width="3" fill="none" stroke-linecap="round"/>` +
    `<circle cx="46" cy="110" r="10" fill="${PIPI}" opacity="0.6"/>` +
    `<circle cx="154" cy="110" r="10" fill="${PIPI}" opacity="0.6"/>` +
    mata(70, 88, p) +
    mata(130, 88, p) +
    alis(70, 130, 62, p) +
    `<path d="M93 106 Q100 100 107 106 Q100 115 93 106 Z" fill="#FF7A9A" stroke="${GELAP}" stroke-width="3" stroke-linejoin="round"/>` +
    mikoMulut(p);
  return bungkus(isi, gradien(p.utama));
};

export const svgKarakter = (nama: string, p: ParamKarakter): string => {
  if (nama === "bolt") return bolt(p);
  if (nama === "miko") return miko(p);
  return mimo(p);
};
