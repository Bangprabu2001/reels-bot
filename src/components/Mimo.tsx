import React, { useContext } from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { Ekspresi } from "../types";
import { SceneContext } from "./SceneContext";
import { svgKarakter } from "./karakter";

// Karakter pendamping (mimo / bolt / miko, dipilih lewat field "karakter").
// Mulut bergerak saat ada kata yang diucapkan, berkedip, dan lengan melambai.
export const Mimo: React.FC<{
  bicara: boolean;
  ekspresi?: Ekspresi;
  ukuran?: number;
}> = ({ bicara, ekspresi = "senang", ukuran = 210 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { karakter } = useContext(SceneContext);

  const masuk = spring({ frame, fps, config: { damping: 9, stiffness: 150 } });
  const naikTurun = Math.sin(frame / 9) * 5;
  const kedip = frame % 96 > 90 ? 0.1 : 1;
  const mulut = bicara ? 0.25 + 0.75 * Math.abs(Math.sin(frame * 0.85)) : 0;
  const lambai = bicara ? 14 + Math.sin(frame / 3.2) * 16 : 0;

  const svg = svgKarakter(karakter ?? "mimo", {
    bicara: mulut,
    kedip,
    ekspresi,
    lambai,
    fase: frame,
    utama: theme.karakterUtama,
    aksen: theme.karakterAksen,
    cahaya: theme.karakterCahaya,
  });

  return (
    <div
      style={{
        width: ukuran,
        height: ukuran,
        flexShrink: 0,
        transform: `translateY(${naikTurun}px) scale(${masuk})`,
        transformOrigin: "50% 100%",
      }}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
