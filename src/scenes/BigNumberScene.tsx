import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { theme } from "../theme";
import type { BigNumberScene as Props } from "../types";

const format = (n: number, bulat: boolean) =>
  bulat
    ? Math.round(n).toLocaleString("id-ID")
    : n.toLocaleString("id-ID", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const BigNumberScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bulat = Number.isInteger(scene.angka);

  const hitung = spring({
    frame: Math.max(0, frame - 14),
    fps,
    config: { damping: 200 },
    durationInFrames: 60,
  });
  const pop = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: { damping: 9, stiffness: 140 },
  });

  const akhir = format(scene.angka, bulat);
  const ukuran = Math.min(250, Math.floor(900 / Math.max(1, akhir.length) / 0.58));

  return (
    <Background>
      <div
        style={{
          width: "100%",
          textAlign: "center",
          fontFamily: theme.font,
          color: theme.text,
        }}
      >
        <div style={{ marginBottom: 50 }}>
          <KineticText text={scene.judul} size={64} stagger={3} />
        </div>
        <div
          style={{
            transform: `scale(${0.7 + 0.3 * pop})`,
            opacity: Math.min(1, pop),
          }}
        >
          <div
            style={{
              fontSize: ukuran,
              fontWeight: 700,
              color: theme.accent,
              lineHeight: 1,
            }}
          >
            {format(scene.angka * hitung, bulat)}
          </div>
          {scene.satuan ? (
            <div
              style={{
                fontSize: 72,
                fontWeight: 600,
                color: theme.accent2,
                marginTop: 10,
              }}
            >
              {scene.satuan}
            </div>
          ) : null}
        </div>
        <div
          style={{
            marginTop: 50,
            fontSize: 52,
            fontWeight: 600,
            lineHeight: 1.3,
            opacity: Math.min(1, Math.max(0, (frame - 40) / 12)),
          }}
        >
          {scene.keterangan}
        </div>
      </div>
    </Background>
  );
};
