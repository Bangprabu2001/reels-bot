import React from "react";
import { Background } from "../components/Background";
import type { CeritaScene as Props } from "../types";

// Scene bercerita: hanya ilustrasi (subtitle digambar terpisah di tengah layar).
export const CeritaScene: React.FC<{ scene: Props }> = () => <Background>{null}</Background>;
