import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { Sfx } from "./Sfx";

// Label istilah kunci (muncul memantul di bagian atas) dan stiker emoji yang bergoyang.
export const KataKunci: React.FC<{ kunci?: string; stiker?: string }> = ({
  kunci,
  stiker,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!kunci && !stiker) return null;

  const label = spring({ frame: Math.max(0, frame - 14), fps, config: { damping: 9, stiffness: 140 } });
  const emoji = spring({ frame: Math.max(0, frame - 26), fps, config: { damping: 7, stiffness: 120 } });

  return (
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 230, pointerEvents: "none" }}>
      {kunci ? (
        <>
          <Sfx nama="pop" dari={14} volume={0.25} />
          <div
            style={{
              fontFamily: theme.font,
              fontWeight: 700,
              fontSize: 72,
              textTransform: theme.caps ? "uppercase" : "none",
              letterSpacing: theme.tracking,
              color: theme.teksDiAksen,
              background: theme.accent,
              padding: "14px 40px",
              borderRadius: 30,
              border: `5px solid ${theme.garis}`,
              boxShadow: "0 10px 0 rgba(0,0,0,0.5)",
              opacity: Math.min(1, label),
              transform: `scale(${label}) rotate(${(1 - label) * -8}deg)`,
              maxWidth: 940,
              textAlign: "center",
              lineHeight: 1.1,
            }}
          >
            {kunci}
          </div>
        </>
      ) : null}
      {stiker ? (
        <div
          style={{
            position: "absolute",
            right: 70,
            top: 520,
            fontSize: 150,
            filter: "drop-shadow(0 8px 0 rgba(0,0,0,0.45))",
            opacity: Math.min(1, emoji),
            transform: `scale(${emoji}) rotate(${Math.sin(frame / 8) * 9}deg)`,
          }}
        >
          {stiker}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
