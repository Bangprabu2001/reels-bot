import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { Sfx } from "../components/Sfx";
import { theme } from "../theme";
import type { PertanyaanScene as Props } from "../types";

// Tanda tanya raksasa yang berputar masuk, lalu pertanyaannya.
export const PertanyaanScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: { damping: 7, stiffness: 110 },
  });

  return (
    <Background>
      <Sfx nama="pop" dari={4} volume={0.3} />
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontFamily: theme.font,
            fontWeight: 700,
            fontSize: 340,
            lineHeight: 1,
            color: theme.accent,
            textShadow: "0 12px 0 rgba(0,0,0,0.6), 0 0 40px rgba(0,0,0,0.8)",
            WebkitTextStroke: `6px ${theme.teksTepi}`,
            paintOrder: "stroke fill",
            transform: `scale(${s}) rotate(${(1 - s) * 20 + Math.sin(frame / 10) * 4}deg)`,
          }}
        >
          ?
        </div>
        <div style={{ marginTop: 20 }}>
          <KineticText text={scene.teks} size={88} stagger={3} />
        </div>
      </div>
    </Background>
  );
};
