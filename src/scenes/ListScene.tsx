import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { theme } from "../theme";
import type { ListScene as Props } from "../types";

export const ListScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <Background>
      <div style={{ width: "100%", fontFamily: theme.font, color: theme.text }}>
        <div style={{ marginBottom: 70 }}>
          <KineticText text={scene.judul} size={78} stagger={3} />
        </div>
        {scene.poin.map((p, i) => {
          const s = spring({
            frame: Math.max(0, frame - 20 - i * 16),
            fps,
            config: { damping: 13, stiffness: 150 },
          });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 32,
                marginBottom: 36,
                padding: "30px 36px",
                borderRadius: 36,
                background: "rgba(255,255,255,0.1)",
                opacity: Math.min(1, s),
                transform: `translateX(${(1 - s) * -220}px)`,
              }}
            >
              <span style={{ fontSize: 88 }}>{p.ikon}</span>
              <span style={{ fontSize: 50, fontWeight: 600, lineHeight: 1.25 }}>
                {p.teks}
              </span>
            </div>
          );
        })}
      </div>
    </Background>
  );
};
