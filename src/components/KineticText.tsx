import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

// Kata muncul satu per satu. Kata yang diapit *bintang* diberi warna aksen.
export const KineticText: React.FC<{
  text: string;
  size?: number;
  stagger?: number; // jeda antar kata (frame)
}> = ({ text, size = 104, stagger = 4 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

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
        textShadow: "0 6px 0 rgba(0,0,0,0.6), 0 0 28px rgba(0,0,0,0.75)",
        WebkitTextStroke: "2px rgba(0,0,0,0.5)",
        paintOrder: "stroke fill",
      }}
    >
      {text.split(" ").map((w, i) => {
        const hl = w.length > 2 && w.startsWith("*") && w.endsWith("*");
        const word = hl ? w.slice(1, -1) : w;
        const s = spring({
          frame: Math.max(0, frame - i * stagger),
          fps,
          config: { damping: 11, stiffness: 190 },
        });
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              opacity: Math.min(1, s),
              transform: `translateY(${(1 - s) * 50}px) scale(${0.6 + 0.4 * s})`,
              color: hl ? theme.accent : theme.text,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
