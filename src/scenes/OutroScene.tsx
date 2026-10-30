import React from "react";
import { useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import { Sfx } from "../components/Sfx";
import type { OutroScene as Props } from "../types";

export const OutroScene: React.FC<{ scene: Props }> = ({ scene }) => {
  const frame = useCurrentFrame();
  return (
    <Background>
      <Sfx nama="ding" dari={8} volume={0.3} />
      <div style={{ textAlign: "center" }}>
        <KineticText text={scene.teks} size={100} />
        <div
          style={{
            fontSize: 150,
            marginTop: 50,
            transform: `scale(${1 + 0.12 * Math.sin(frame / 5)}) rotate(${Math.sin(frame / 4) * 8}deg)`,
          }}
        >
          🔔
        </div>
      </div>
    </Background>
  );
};
