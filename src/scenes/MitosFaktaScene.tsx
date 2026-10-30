import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { Sfx } from "../components/Sfx";
import { theme } from "../theme";
import type { MitosFaktaScene as Props } from "../types";

// Kartu MITOS dicoret, lalu kartu FAKTA masuk.
export const MitosFaktaScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const mitos = spring({ frame: Math.max(0, frame - 6), fps, config: { damping: 12 } });
  const coret = interpolate(frame, [44, 56], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fakta = spring({
    frame: Math.max(0, frame - 62),
    fps,
    config: { damping: 11, stiffness: 130 },
  });

  const kartu = (warna: string): React.CSSProperties => ({
    padding: "32px 40px",
    borderRadius: 40,
    background: "rgba(255,255,255,0.1)",
    border: `6px solid ${warna}`,
  });

  return (
    <Background>
      <Sfx nama="pop" dari={6} volume={0.3} />
      <Sfx nama="pop" dari={44} volume={0.3} />
      <Sfx nama="ding" dari={62} volume={0.3} />
      <div style={{ width: "100%", fontFamily: theme.font, color: theme.text }}>
        <div
          style={{
            ...kartu(theme.merah),
            opacity: Math.min(1, mitos) * (coret >= 100 ? 0.6 : 1),
            transform: `scale(${0.8 + 0.2 * mitos})`,
          }}
        >
          <div style={{ fontSize: 56, fontWeight: 700, color: theme.merah }}>MITOS ✗</div>
          <div style={{ position: "relative", fontSize: 54, fontWeight: 600, lineHeight: 1.3, marginTop: 10 }}>
            {scene.mitos}
            <div
              style={{
                position: "absolute",
                left: 0,
                top: "50%",
                height: 8,
                width: `${coret}%`,
                background: theme.merah,
                borderRadius: 4,
              }}
            />
          </div>
        </div>
        <div
          style={{
            ...kartu(theme.hijau),
            marginTop: 40,
            opacity: Math.min(1, fakta),
            transform: `translateY(${(1 - fakta) * 300}px)`,
          }}
        >
          <div style={{ fontSize: 56, fontWeight: 700, color: theme.hijau }}>FAKTA ✓</div>
          <div style={{ fontSize: 54, fontWeight: 600, lineHeight: 1.3, marginTop: 10 }}>
            {scene.fakta}
          </div>
        </div>
      </div>
    </Background>
  );
};
