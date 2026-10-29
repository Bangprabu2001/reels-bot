import { createContext } from "react";

// Dipakai agar Background tahu video latar (b-roll) milik scene yang sedang tampil.
export const SceneContext = createContext<{ brollSrc?: string }>({});
