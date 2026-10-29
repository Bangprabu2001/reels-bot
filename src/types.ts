// Skema JSON yang dihasilkan agen. Tiap "type" dipetakan ke satu komponen scene.
export type Kata = { teks: string; mulai: number; selesai: number }; // detik

type Dasar = {
  durasi: number; // detik; diisi ulang oleh agen suara sesuai panjang audio
  narasi: string;
  audioSrc?: string; // relatif ke public/, mis. "audio/topik/scene_0.mp3"
  kata?: Kata[]; // timestamp per kata untuk subtitle
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

export type Scene = HookScene | BarChartScene | ListScene;

export type VideoProps = {
  scenes: Scene[];
  musikSrc?: string; // musik latar opsional di public/, volume dibuat kecil
};
