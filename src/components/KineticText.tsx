import React, { useContext } from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { SceneContext } from "./SceneContext";

// Kata yang diapit *bintang* diberi warna aksen. Gaya muncul mengikuti gaya video:
// 0 memantul/menempel, 1 masuk dari samping, 2 diketik.
export const KineticText: React.FC<{
  text: string;
  size?: number;
  stagger?: number; // jeda antar kata (frame)
}> = ({ text, size = 104, stagger = 4 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  useContext(SceneContext);
  const gaya = theme.teksGaya;
  const huruf = Math.floor(frame * 1.4);
  const clay = theme.kode === "STYLE_CLAY_3D";
  let offset = 0;

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: "0 26px",
        fontFamily: theme.font,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.15,
        textAlign: "center",
        color: theme.text,
        textTransform: theme.caps ? "uppercase" : "none",
        letterSpacing: theme.tracking,
        textShadow: theme.teksBayang,
        WebkitTextStroke: `4px ${theme.teksTepi}`,
        paintOrder: "stroke fill",
      }}
    >
      {text.split(" ").map((w, i) => {
        const hl = w.length > 2 && w.startsWith("*") && w.endsWith("*");
        const word = hl ? w.slice(1, -1) : w;
        const s = spring({
          frame: Math.max(0, frame - i * stagger),
          fps,
          config: clay ? { damping: 6, stiffness: 170 } : { damping: 11, stiffness: 190 },
        });
        const mulai = offset;
        offset += word.length + 1;

        let isi: React.ReactNode = word;
        let gayaKata: React.CSSProperties;
        if (gaya === 2) {
          const n = Math.max(0, Math.min(word.length, huruf - mulai));
          isi = (
            <>
              {word.slice(0, n)}
              <span style={{ visibility: "hidden" }}>{word.slice(n)}</span>
            </>
          );
          gayaKata = {};
        } else if (gaya === 1) {
          const arah = i % 2 ? 1 : -1;
          gayaKata = {
            opacity: Math.min(1, s),
            transform: `translateX(${(1 - s) * 180 * arah}px) rotate(${(1 - s) * 8 * arah}deg)`,
          };
        } else {
          gayaKata = {
            opacity: Math.min(1, s * 1.5),
            transform: `translateY(${(1 - s) * 40}px) scale(${theme.popAwal + (1 - theme.popAwal) * s})`,
          };
        }

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              color: hl ? theme.accent : theme.text,
              ...gayaKata,
            }}
          >
            {isi}
          </span>
        );
      })}
    </div>
  );
};
