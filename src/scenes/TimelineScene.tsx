import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { theme } from "../theme";
import type { TimelineScene as Props } from "../types";

export const TimelineScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const garis = spring({
    frame: Math.max(0, frame - 12),
    fps,
    config: { damping: 200 },
    durationInFrames: 20 + scene.langkah.length * 18,
  });

  return (
    <Background>
      <div style={{ width: "100%", fontFamily: theme.font, color: theme.text }}>
        <div style={{ marginBottom: 60 }}>
          <KineticText text={scene.judul} size={68} stagger={3} />
        </div>
        <div style={{ position: "relative", paddingLeft: 110 }}>
          {/* garis vertikal yang tergambar bertahap */}
          <div
            style={{
              position: "absolute",
              left: 27,
              top: 30,
              bottom: 30,
              width: 8,
              borderRadius: 4,
              background: theme.accent2,
              transformOrigin: "top",
              transform: `scaleY(${garis})`,
            }}
          />
          {scene.langkah.map((l, i) => {
            const s = spring({
              frame: Math.max(0, frame - 20 - i * 18),
              fps,
              config: { damping: 12, stiffness: 150 },
            });
            return (
              <div
                key={i}
                style={{
                  position: "relative",
                  marginBottom: 34,
                  opacity: Math.min(1, s),
                  transform: `translateX(${(1 - s) * 120}px)`,
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    left: -110,
                    top: 6,
                    width: 62,
                    height: 62,
                    borderRadius: "50%",
                    background: theme.accent,
                    border: `8px solid ${theme.bg1}`,
                    boxSizing: "border-box",
                    transform: `scale(${s})`,
                  }}
                />
                <div style={{ fontSize: 44, fontWeight: 700, color: theme.accent }}>
                  {l.label}
                </div>
                <div style={{ fontSize: 46, fontWeight: 600, lineHeight: 1.25 }}>
                  {l.teks}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Background>
  );
};
