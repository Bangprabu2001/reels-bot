import React, { useContext } from "react";
import { Audio, Sequence, staticFile } from "remotion";
import { theme } from "../theme";
import { SceneContext } from "./SceneContext";

// Efek suara singkat. Nama logis (whoosh/pop/ding) diterjemahkan sesuai gaya video:
// HUD = tick digital, Kertas = gemerisik, Noir = ketikan mesin tik, Clay = pop.
export const Sfx: React.FC<{
  nama: "whoosh" | "pop" | "ding";
  dari?: number;
  volume?: number;
}> = ({ nama, dari = 0, volume = 0.4 }) => {
  const { sfx } = useContext(SceneContext);
  const file = sfx?.[theme.sfxPeta[nama] ?? nama] ?? sfx?.[nama];
  if (!file) return null;
  return (
    <Sequence from={dari} durationInFrames={90} layout="none">
      <Audio src={staticFile(file)} volume={volume} />
    </Sequence>
  );
};
