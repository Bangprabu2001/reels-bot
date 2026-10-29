// Skema JSON yang dihasilkan agen. Tiap "type" dipetakan ke satu komponen scene.
export type Kata = { teks: string; mulai: number; selesai: number }; // detik
export type Ekspresi = "senang" | "kaget" | "mikir";

type Dasar = {
  durasi: number; // detik; diisi ulang oleh agen suara sesuai panjang audio
  narasi: string;
  audioSrc?: string; // relatif ke public/, mis. "audio/topik/scene_0.mp3"
  kata?: Kata[]; // timestamp per kata untuk subtitle dan gerak mulut maskot
  ekspresi?: Ekspresi; // ekspresi maskot Mimo
  broll?: string[]; // kata kunci pencarian video stok (bahasa Inggris), diisi agen
  brollSrc?: string; // file video latar di public/, diisi agen b-roll
};

export type HookScene = Dasar & {
  type: "hook";
  teks: string; // kata penting diapit *bintang*
};

export type BarChartScene = Dasar & {
  type: "bar_chart";
  judul: string;
  data: { label: string; nilai: number }[];
  satuan?: string;
};

export type ListScene = Dasar & {
  type: "list";
  judul: string;
  poin: { ikon: string; teks: string }[]; // ikon = emoji
};

export type BigNumberScene = Dasar & {
  type: "big_number";
  judul: string;
  angka: number;
  satuan?: string;
  keterangan: string;
};

export type Sisi = { nama: string; poin: string[] };

export type CompareScene = Dasar & {
  type: "compare";
  judul: string;
  kiri: Sisi;
  kanan: Sisi;
};

export type TimelineScene = Dasar & {
  type: "timeline";
  judul: string;
  langkah: { label: string; teks: string }[];
};

export type FaktaScene = Dasar & {
  type: "fakta";
  teks: string; // kata penting diapit *bintang*
  ikon: string; // satu emoji besar
};

export type MitosFaktaScene = Dasar & {
  type: "mitos_fakta";
  mitos: string;
  fakta: string;
};

export type OutroScene = Dasar & {
  type: "outro";
  teks: string;
};

export type Scene =
  | HookScene
  | BarChartScene
  | ListScene
  | BigNumberScene
  | CompareScene
  | TimelineScene
  | FaktaScene
  | MitosFaktaScene
  | OutroScene;

export type VideoProps = {
  scenes: Scene[];
  musikSrc?: string; // musik latar opsional di public/, volume dibuat kecil
  sfx?: boolean; // true bila efek suara (public/sfx/*.wav) tersedia
};
