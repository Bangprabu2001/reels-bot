import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { theme } from "../theme";

export const Background: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const frame = useCurrentFrame();
  const { top, bottom, side } = theme.safe;

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${150 + Math.sin(frame / 90) * 12}deg, ${theme.bg1}, ${theme.bg2})`,
      }}
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            width: 520,
            height: 520,
            borderRadius: "50%",
            background: i === 1 ? theme.accent2 : theme.accent,
            opacity: 0.07,
            left: 60 + i * 330 + Math.sin((frame + i * 70) / 55) * 70,
            top: 250 + i * 520 + Math.cos((frame + i * 40) / 65) * 90,
          }}
        />
      ))}
      <AbsoluteFill
        style={{
          padding: `${top}px ${side}px ${bottom}px`,
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
