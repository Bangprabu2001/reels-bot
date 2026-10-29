import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { Sfx } from "../components/Sfx";
import type { FaktaScene as Props } from "../types";

// Pernyataan singkat dengan emoji besar yang muncul berputar.
export const FaktaScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 7, stiffness: 120 } });

  return (
    <Background>
      <Sfx nama="pop" dari={4} volume={0.35} />
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontSize: 230,
            marginBottom: 30,
            transform: `scale(${s}) rotate(${(1 - s) * -40}deg)`,
          }}
        >
          {scene.ikon}
        </div>
        <KineticText text={scene.teks} size={92} stagger={3} />
      </div>
    </Background>
  );
};
