import React from "react";
import { Background } from "../components/Background";
import { KineticText } from "../components/KineticText";
import type { HookScene as Props } from "../types";

export const HookScene: React.FC<{ scene: Props }> = ({ scene }) => (
  <Background>
    <KineticText text={scene.teks} size={116} />
  </Background>
);
