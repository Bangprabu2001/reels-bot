import { createContext } from "react";

// Info yang dibagikan ke scene yang sedang tampil.
export const SceneContext = createContext<{
  gambarSrc?: string; // ilustrasi kartun latar
  brollSrc?: string; // (opsional, lama) video latar
  indeks?: number; // urutan scene, untuk variasi arah gerak kamera
  redup?: number; // 0..1 seberapa gelap lapisan di atas ilustrasi
  sfx?: Record<string, string>; // peta nama efek suara -> file
}>({});
