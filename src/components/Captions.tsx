import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { Kata } from "../types";

const PER_BARIS = 4; // jumlah kata yang tampil sekaligus

export const Captions: React.FC<{ kata?: Kata[] }> = ({ kata }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!kata || kata.length === 0) return null;

  const t = frame / fps;
  const kelompok: Kata[][] = [];
  for (let i = 0; i < kata.length; i += PER_BARIS) {
    kelompok.push(kata.slice(i, i + PER_BARIS));
  }
  let idx = 0;
  kelompok.forEach((k, i) => {
    if (k[0].mulai <= t) idx = i;
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 300,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 18px",
          fontFamily: theme.font,
          fontWeight: 700,
          fontSize: 62,
          textAlign: "center",
          padding: "14px 32px",
          borderRadius: 28,
          background: "rgba(10,16,50,0.55)",
        }}
      >
        {kelompok[idx].map((w, i) => {
          const aktif = t >= w.mulai && t < w.selesai;
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                color: aktif ? theme.accent : theme.text,
                transform: `scale(${aktif ? 1.12 : 1})`,
              }}
            >
              {w.teks}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
