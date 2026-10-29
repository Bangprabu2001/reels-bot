import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { Sfx } from "../components/Sfx";
import { theme } from "../theme";
import type { BarChartScene as Props } from "../types";

export const BarChartScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const max = Math.max(...scene.data.map((d) => d.nilai), 1);

  return (
    <Background>
      {scene.data.map((_, i) => (
        <Sfx key={i} nama="pop" dari={18 + i * 9} volume={0.2} />
      ))}
      <div style={{ width: "100%", fontFamily: theme.font, color: theme.text }}>
        <div style={{ marginBottom: 70 }}>
          <KineticText text={scene.judul} size={70} stagger={3} />
        </div>
        {scene.data.map((d, i) => {
          const p = spring({
            frame: Math.max(0, frame - 18 - i * 9),
            fps,
            config: { damping: 200 },
          });
          return (
            <div key={d.label} style={{ marginBottom: 44 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 46,
                  fontWeight: 600,
                  marginBottom: 12,
                }}
              >
                <span>{d.label}</span>
                <span style={{ color: theme.accent }}>
                  {Math.round(d.nilai * p)} {scene.satuan ?? ""}
                </span>
              </div>
              <div
                style={{
                  height: 46,
                  borderRadius: 23,
                  background: "rgba(255,255,255,0.12)",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${(d.nilai / max) * 100 * p}%`,
                    borderRadius: 23,
                    background:
                      i === 0
                        ? theme.accent
                        : `linear-gradient(90deg, ${theme.accent2}, #7C9BFF)`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Background>
  );
};
