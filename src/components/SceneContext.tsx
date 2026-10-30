import { createContext } from "react";

// Info yang dibagikan ke scene yang sedang tampil.
export const SceneContext = createContext<{
  brollSrc?: string; // video latar (b-roll)
  sfx?: Record<string, string>; // peta nama efek suara -> file
  karakter?: string; // mimo | bolt | miko
}>({});
