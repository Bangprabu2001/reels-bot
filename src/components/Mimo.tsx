import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { Ekspresi } from "../types";

// Maskot "Mimo": mulutnya bergerak saat ada kata yang diucapkan, bisa berkedip,
// dan ekspresinya mengikuti field "ekspresi" di naskah.
export const Mimo: React.FC<{
  bicara: boolean;
  ekspresi?: Ekspresi;
  ukuran?: number;
}> = ({ bicara, ekspresi = "senang", ukuran = 210 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const masuk = spring({ frame, fps, config: { damping: 9, stiffness: 150 } });
  const naikTurun = Math.sin(frame / 9) * 5;
  const kedip = frame % 90 > 85 ? 0.12 : 1;
  const kaget = ekspresi === "kaget";
  const mulut = bicara ? 6 + 16 * Math.abs(Math.sin(frame * 0.85)) : 3;
  const mata = kaget ? 17 : 12;
  const gelap = "#1B1F3B";

  return (
    <svg
      width={ukuran}
      height={ukuran}
      viewBox="0 0 200 200"
      style={{
        flexShrink: 0,
        transform: `translateY(${naikTurun}px) scale(${masuk})`,
        transformOrigin: "50% 100%",
      }}
    >
      {/* tunas di kepala */}
      <path
        d="M100 42 Q96 22 112 14"
        stroke={theme.accent2}
        strokeWidth="8"
        fill="none"
        strokeLinecap="round"
      />
      <circle cx="114" cy="14" r="9" fill={theme.accent2} />
      {/* badan */}
      <ellipse cx="100" cy="116" rx="78" ry="74" fill={theme.accent} />
      {/* pipi */}
      <circle cx="46" cy="130" r="12" fill="#FF9E7A" opacity="0.7" />
      <circle cx="154" cy="130" r="12" fill="#FF9E7A" opacity="0.7" />
      {/* mata */}
      <ellipse cx="72" cy="100" rx={mata} ry={mata * kedip} fill="#fff" />
      <ellipse cx="128" cy="100" rx={mata} ry={mata * kedip} fill="#fff" />
      <ellipse cx="74" cy="102" rx={mata * 0.5} ry={mata * 0.5 * kedip} fill={gelap} />
      <ellipse cx="130" cy="102" rx={mata * 0.5} ry={mata * 0.5 * kedip} fill={gelap} />
      {/* alis */}
      {ekspresi === "mikir" ? (
        <path d="M54 76 Q72 64 90 78" stroke={gelap} strokeWidth="5" fill="none" strokeLinecap="round" />
      ) : null}
      {kaget ? (
        <>
          <path d="M52 72 Q72 56 92 72" stroke={gelap} strokeWidth="5" fill="none" strokeLinecap="round" />
          <path d="M108 72 Q128 56 148 72" stroke={gelap} strokeWidth="5" fill="none" strokeLinecap="round" />
        </>
      ) : null}
      {/* mulut */}
      {bicara || kaget ? (
        <ellipse
          cx="100"
          cy="146"
          rx={kaget ? 11 : 15}
          ry={kaget ? 15 : mulut}
          fill="#7A1F2B"
        />
      ) : (
        <path d="M78 142 Q100 160 122 142" stroke={gelap} strokeWidth="6" fill="none" strokeLinecap="round" />
      )}
    </svg>
  );
};
