import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { Ekspresi, Kata } from "../types";
import { Mimo } from "./Mimo";

const PER_BARIS = 3; // jumlah kata yang tampil sekaligus

// Baris bawah layar: maskot Mimo di kiri, subtitle animasi di kanan.
export const BawahLayar: React.FC<{
  kata?: Kata[];
  ekspresi?: Ekspresi;
  caption: boolean;
}> = ({ kata, ekspresi, caption }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const bicara = !!kata?.some((w) => t >= w.mulai - 0.02 && t < w.selesai + 0.05);

  let kelompok: Kata[][] = [];
  let idx = 0;
  if (caption && kata && kata.length > 0) {
    for (let i = 0; i < kata.length; i += PER_BARIS) {
      kelompok.push(kata.slice(i, i + PER_BARIS));
    }
    kelompok.forEach((k, i) => {
      if (k[0].mulai <= t) idx = i;
    });
  }
  const sekarang = kelompok[idx];

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 330,
        paddingLeft: 50,
        paddingRight: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 24, width: "100%" }}>
        <Mimo bicara={bicara} ekspresi={ekspresi} />
        {sekarang ? (
          <div
            style={{
              flex: 1,
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              gap: "0 16px",
              fontFamily: theme.font,
              fontWeight: 700,
              fontSize: 54,
              lineHeight: 1.2,
              textAlign: "center",
              padding: "16px 26px",
              borderRadius: 30,
              background: "rgba(10,16,50,0.6)",
            }}
          >
            {sekarang.map((w, i) => {
              const aktif = t >= w.mulai && t < w.selesai;
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    color: aktif ? theme.accent : theme.text,
                    transform: `scale(${aktif ? 1.1 : 1})`,
                  }}
                >
                  {w.teks}
                </span>
              );
            })}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
