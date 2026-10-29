import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { Sfx } from "../components/Sfx";
import { theme } from "../theme";
import type { CompareScene as Props, Sisi } from "../types";

const Kartu: React.FC<{
  sisi: Sisi;
  warna: string;
  dari: number;
  tunda: number;
}> = ({ sisi, warna, dari, tunda }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({
    frame: Math.max(0, frame - tunda),
    fps,
    config: { damping: 14, stiffness: 130 },
  });
  return (
    <div
      style={{
        padding: "30px 40px",
        borderRadius: 40,
        background: "rgba(255,255,255,0.1)",
        border: `6px solid ${warna}`,
        transform: `translateX(${(1 - s) * dari}px)`,
        opacity: Math.min(1, s),
      }}
    >
      <div style={{ fontSize: 60, fontWeight: 700, color: warna, marginBottom: 10 }}>
        {sisi.nama}
      </div>
      {sisi.poin.map((p, i) => (
        <div key={i} style={{ fontSize: 44, fontWeight: 600, lineHeight: 1.3, marginTop: 6 }}>
          • {p}
        </div>
      ))}
    </div>
  );
};

export const CompareScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const vs = spring({
    frame: Math.max(0, frame - 34),
    fps,
    config: { damping: 8, stiffness: 160 },
  });

  return (
    <Background>
      <Sfx nama="pop" dari={16} volume={0.25} />
      <Sfx nama="pop" dari={26} volume={0.25} />
      <Sfx nama="pop" dari={34} volume={0.3} />
      <div style={{ width: "100%", fontFamily: theme.font, color: theme.text }}>
        <div style={{ marginBottom: 50 }}>
          <KineticText text={scene.judul} size={66} stagger={3} />
        </div>
        <Kartu sisi={scene.kiri} warna={theme.accent2} dari={-900} tunda={16} />
        <div
          style={{
            width: 104,
            height: 104,
            borderRadius: "50%",
            background: theme.accent,
            color: theme.bg1,
            fontSize: 54,
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "-22px auto",
            position: "relative",
            zIndex: 2,
            transform: `scale(${vs})`,
          }}
        >
          VS
        </div>
        <Kartu sisi={scene.kanan} warna={theme.accent} dari={900} tunda={26} />
      </div>
    </Background>
  );
};
