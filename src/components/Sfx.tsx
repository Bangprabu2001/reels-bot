import React, { useContext } from "react";
import { Audio, Sequence, staticFile } from "remotion";
import { SceneContext } from "./SceneContext";

// Efek suara singkat. Tidak menampilkan apa pun; hanya memutar audio pada frame "dari".
export const Sfx: React.FC<{
  nama: "whoosh" | "pop" | "ding";
  dari?: number;
  volume?: number;
}> = ({ nama, dari = 0, volume = 0.4 }) => {
  const { sfx } = useContext(SceneContext);
  const file = sfx?.[nama];
  if (!file) return null;
  return (
    <Sequence from={dari} durationInFrames={90} layout="none">
      <Audio src={staticFile(file)} volume={volume} />
    </Sequence>
  );
};
