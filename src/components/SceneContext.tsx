import { createContext } from "react";

// Info yang dibagikan ke scene yang sedang tampil.
export const SceneContext = createContext<{
  gambarSrc?: string; // ilustrasi latar scene
  indeks?: number; // urutan scene, untuk variasi gerak dan transisi
  awal?: number; // frame awal scene dalam seluruh video (untuk penghitung waktu HUD)
  redup?: number; // 0..1 seberapa pekat lapisan di atas ilustrasi
  sfx?: Record<string, string>; // peta nama efek suara -> file
}>({});
