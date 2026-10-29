import { createContext } from "react";

// Info scene yang sedang tampil: video latar (b-roll) dan apakah efek suara tersedia.
export const SceneContext = createContext<{ brollSrc?: string; sfx?: boolean }>({});
