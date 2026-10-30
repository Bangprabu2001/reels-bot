// Skema JSON yang dihasilkan agen. Tiap "type" dipetakan ke satu komponen scene.
export type Kata = { teks: string; mulai: number; selesai: number }; // detik

type Dasar = {
  durasi: number; // detik; diisi ulang oleh agen suara sesuai panjang audio
  narasi: string;
  audioSrc?: string; // relatif ke public/, mis. "audio/topik/scene_0.mp3"
  kata?: Kata[]; // timestamp per kata untuk subtitle dan gerak mulut maskot
  gambar?: string; // prompt ilustrasi (bahasa Inggris), diisi agen naskah
  gambarSrc?: string; // file ilustrasi di public/, diisi agen ilustrator
  broll?: string[]; // (opsional, lama) kata kunci video stok
  brollSrc?: string; // (opsional, lama) file video latar di public/
};

export type HookScene = Dasar & {
  type: "hook";
  teks: string; // kata penting diapit *bintang*
};

export type CeritaScene = Dasar & {
  type: "cerita"; // hanya narasi di atas ilustrasi, subtitle di tengah layar
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
  | CeritaScene
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
  sfx?: Record<string, string>; // nama efek -> file di public/, mis. {"pop": "sfx/pop.wav"}
  tema?: string; // gelap | neon
};
