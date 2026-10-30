import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { Kata } from "../types";

const PER_BARIS = 3; // sedikit kata sekaligus supaya gambar tetap terlihat

// Subtitle di tengah layar tanpa panel: huruf besar bertepi hitam tebal, kata yang diucapkan menyala.
export const SubtitleTengah: React.FC<{ kata?: Kata[] }> = ({ kata }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (!kata || kata.length === 0) return null;

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
      style={{ justifyContent: "center", alignItems: "center", padding: "0 60px" }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 22px",
          fontFamily: theme.font,
          fontWeight: 700,
          fontSize: 84,
          lineHeight: 1.15,
          textAlign: "center",
          textShadow: "0 7px 0 rgba(0,0,0,0.65), 0 0 34px rgba(0,0,0,0.9)",
          WebkitTextStroke: "8px #000000",
          paintOrder: "stroke fill",
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
                transform: `scale(${aktif ? 1.08 : 1})`,
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
