import React, { useContext } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { SceneContext } from "./SceneContext";
import { acak, noiseUri } from "./tekstur";

const CYAN = "#00F0FF";
const MERAH = "#FF3B30";

// HUD: siku bingkai, kotak target merah, label data mengambang, pewaktu digital, gelombang suara.
export const HudOverlay: React.FC<{ label?: string }> = ({ label }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { awal = 0, indeks = 0 } = useContext(SceneContext);

  const waktu = (awal + frame) / fps;
  const mm = String(Math.floor(waktu / 60)).padStart(2, "0");
  const ss = String(Math.floor(waktu % 60)).padStart(2, "0");
  const cs = String(Math.floor((waktu * 100) % 100)).padStart(2, "0");

  const posisi = [[0.24, 0.2], [0.72, 0.24], [0.5, 0.18], [0.3, 0.3], [0.7, 0.3]][indeks % 5];
  const x = posisi[0] * 1080 + Math.sin(frame / 9) * 10;
  const y = posisi[1] * 1920 + Math.cos(frame / 11) * 8;
  const kunci = Math.min(1, frame / 12); // kotak target "mengunci" dari besar ke kecil
  const teksLabel = label ? `[${label}]` : "";
  const huruf = Math.floor(frame * 1.2);

  const siku = (gaya: React.CSSProperties) => (
    <div style={{ position: "absolute", width: 70, height: 70, opacity: 0.7, ...gaya }} />
  );
  const tipis = "2px solid #FFFFFF";

  return (
    <AbsoluteFill style={{ pointerEvents: "none", fontFamily: theme.fontBody }}>
      {siku({ left: 36, top: 150, borderTop: tipis, borderLeft: tipis })}
      {siku({ right: 36, top: 150, borderTop: tipis, borderRight: tipis })}
      {siku({ left: 36, top: 1430, borderBottom: tipis, borderLeft: tipis })}
      {siku({ right: 36, top: 1430, borderBottom: tipis, borderRight: tipis })}

      {/* kotak target / crosshair merah */}
      <div
        style={{
          position: "absolute",
          left: x - 60,
          top: y - 60,
          width: 120,
          height: 120,
          border: `3px solid ${MERAH}`,
          opacity: 0.4 + 0.6 * kunci,
          transform: `scale(${1.8 - 0.8 * kunci})`,
        }}
      >
        <div style={{ position: "absolute", left: "50%", top: -14, width: 2, height: 28, background: MERAH }} />
        <div style={{ position: "absolute", left: "50%", bottom: -14, width: 2, height: 28, background: MERAH }} />
        <div style={{ position: "absolute", top: "50%", left: -14, height: 2, width: 28, background: MERAH }} />
        <div style={{ position: "absolute", top: "50%", right: -14, height: 2, width: 28, background: MERAH }} />
      </div>

      {/* label data mengambang */}
      {teksLabel ? (
        <div
          style={{
            position: "absolute",
            left: 64,
            top: 200,
            fontSize: 30,
            letterSpacing: 4,
            color: CYAN,
            textShadow: `0 0 14px ${CYAN}`,
          }}
        >
          {teksLabel.slice(0, huruf)}
          <span style={{ opacity: frame % 16 < 8 ? 1 : 0 }}>_</span>
        </div>
      ) : null}

      {/* pewaktu digital */}
      <div
        style={{
          position: "absolute",
          right: 64,
          top: 200,
          fontSize: 28,
          letterSpacing: 3,
          color: "#FFFFFF",
          opacity: 0.85,
        }}
      >
        {`T+${mm}:${ss}.${cs}`}
      </div>

      {/* gelombang suara */}
      <div style={{ position: "absolute", left: 64, top: 1340, display: "flex", alignItems: "flex-end", gap: 6, height: 70 }}>
        {Array.from({ length: 22 }, (_, i) => (
          <div
            key={i}
            style={{
              width: 8,
              height: 8 + 58 * Math.abs(Math.sin(frame / 5 + i * 0.7)) * (0.5 + 0.5 * Math.abs(Math.sin(i))),
              background: CYAN,
              opacity: 0.85,
              boxShadow: `0 0 8px ${CYAN}`,
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};

// Noir: butiran film, goresan, kedip proyektor, vinyet gelap.
export const NoirEfek: React.FC = () => {
  const frame = useCurrentFrame();
  const butir = (frame % 4) + 1;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill
        style={{ backgroundImage: noiseUri(butir, 0.9, 1.4, "0.9 0.9 0.9"), opacity: 0.25, mixBlendMode: "overlay" }}
      />
      {[0, 1, 2].map((i) => {
        const langkah = Math.floor(frame / 3);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: acak(langkah * 3 + i) * 1080,
              top: 0,
              bottom: 0,
              width: 2,
              background: "rgba(255,255,255,0.4)",
              opacity: (langkah + i) % 5 === 0 ? 0.85 : 0,
            }}
          />
        );
      })}
      <AbsoluteFill style={{ background: "#000000", opacity: frame % 9 === 0 ? 0.14 : 0 }} />
      <AbsoluteFill
        style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 40%, rgba(0,0,0,0.72) 100%)" }}
      />
    </AbsoluteFill>
  );
};
