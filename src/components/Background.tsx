import React, { useContext } from "react";
import { AbsoluteFill, Img, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { SceneContext } from "./SceneContext";
import { noiseUri, tepiSobekan } from "./tekstur";

const GERAK = ["zoom_in", "pan_kiri", "zoom_out", "pan_kanan", "naik", "turun"];

const kameraTransform = (g: string, f: number): string => {
  switch (g) {
    case "zoom_out":
      return `scale(${Math.max(1.45 - f * 0.0012, 1.12)})`;
    case "pan_kiri":
      return `scale(1.3) translate(${60 - f * 0.3}px, 0px)`;
    case "pan_kanan":
      return `scale(1.3) translate(${-60 + f * 0.3}px, 0px)`;
    case "naik":
      return `scale(1.3) translate(0px, ${50 - f * 0.28}px)`;
    case "turun":
      return `scale(1.3) translate(0px, ${-50 + f * 0.28}px)`;
    default:
      return `scale(${Math.min(1.1 + f * 0.0012, 1.5)})`;
  }
};

const Isi: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { top, bottom, side } = theme.safe;
  return (
    <AbsoluteFill
      style={{
        padding: `${top}px ${side}px ${bottom}px`,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const penuh: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };

// ---------- 1. HUD: hitam, titik-titik halus, garis tipis, garis pindai ----------
const LatarHud: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { gambarSrc, indeks = 0, redup = 0.5 } = useContext(SceneContext);
  const kamera = kameraTransform(GERAK[(indeks * 5 + 1) % GERAK.length], frame);
  return (
    <AbsoluteFill style={{ background: "#000000" }}>
      <AbsoluteFill
        style={{
          backgroundImage: "radial-gradient(#1A1A1A 2px, transparent 2.5px)",
          backgroundSize: "44px 44px",
        }}
      />
      {gambarSrc ? (
        <Img
          src={staticFile(gambarSrc)}
          style={{
            ...penuh,
            mixBlendMode: "screen", // bagian hitam gambar menyatu dengan latar
            transform: kamera,
            opacity: 1 - redup * 0.85,
            filter: "drop-shadow(0 0 10px rgba(0,240,255,0.55))",
          }}
        />
      ) : null}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: ((frame * 10) % 2200) - 140,
          height: 4,
          background: "linear-gradient(90deg, transparent, rgba(0,240,255,0.9), transparent)",
          opacity: 0.28,
          boxShadow: "0 0 24px rgba(0,240,255,0.8)",
        }}
      />
      <Isi>{children}</Isi>
    </AbsoluteFill>
  );
};

// ---------- 2. Kertas: krem bertekstur, sobekan, selotip, foto tempel ----------
const Selotip: React.FC<{ warna: string; gaya: React.CSSProperties }> = ({ warna, gaya }) => (
  <div
    style={{
      position: "absolute",
      width: 210,
      height: 56,
      background: warna,
      opacity: 0.88,
      backgroundImage: "repeating-linear-gradient(45deg, rgba(255,255,255,0.35) 0 10px, transparent 10px 20px)",
      boxShadow: "0 3px 6px rgba(0,0,0,0.2)",
      ...gaya,
    }}
  />
);

const LatarKertas: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { gambarSrc, indeks = 0, redup = 0.5 } = useContext(SceneContext);
  const miring = (indeks % 2 ? 1.4 : -1.6) + Math.sin(frame / 70) * 0.7;
  const geser = `scale(1.15) translate(${Math.sin(frame / 90) * 14}px, ${-frame * 0.05}px)`;
  return (
    <AbsoluteFill style={{ background: theme.bg1 }}>
      <AbsoluteFill
        style={{
          backgroundImage: noiseUri(3, 0.8, 0.5, "0.35 0.28 0.18"),
          opacity: 0.5,
          mixBlendMode: "multiply",
        }}
      />
      {/* sobekan kertas atas dan bawah */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 100, background: "#E2D8C0", clipPath: tepiSobekan(indeks + 2, false) }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 100, background: "#E2D8C0", clipPath: tepiSobekan(indeks + 9, true) }} />
      {gambarSrc ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div style={{ position: "relative", width: 900, height: 1340, transform: `rotate(${miring}deg)` }}>
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "#FFFDF7",
                borderRadius: 12,
                boxShadow: "0 18px 34px rgba(60,40,20,0.35)",
                padding: 18,
              }}
            >
              <div style={{ width: "100%", height: "100%", overflow: "hidden", position: "relative" }}>
                <Img src={staticFile(gambarSrc)} style={{ ...penuh, transform: geser }} />
                <AbsoluteFill style={{ background: `rgba(${theme.redupRgb},${redup})` }} />
              </div>
            </div>
            <Selotip warna="#A8B5A2" gaya={{ top: -26, left: 40, transform: "rotate(-8deg)" }} />
            <Selotip warna="#D9B166" gaya={{ top: -26, right: 40, transform: "rotate(7deg)" }} />
          </div>
        </AbsoluteFill>
      ) : null}
      {/* coretan pensil dan bintang kecil */}
      <svg style={{ position: "absolute", top: 120, right: 70 }} width="170" height="60" viewBox="0 0 170 60">
        <path d="M5 40 Q30 5 55 40 T105 40 T165 40" stroke="#1A1A1A" strokeWidth="4" fill="none" strokeLinecap="round" opacity="0.5" />
      </svg>
      <div style={{ position: "absolute", left: 60, top: 150, fontSize: 56, color: "#D9B166", transform: `rotate(${Math.sin(frame / 20) * 10}deg)` }}>★</div>
      <div style={{ position: "absolute", right: 80, bottom: 150, fontSize: 46, color: "#C67C5A", transform: `rotate(${Math.cos(frame / 22) * 12}deg)` }}>★</div>
      <Isi>{children}</Isi>
    </AbsoluteFill>
  );
};

// ---------- 3. Noir: koran tua, foto fotokopi hitam putih, halftone ----------
const LatarNoir: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { gambarSrc, indeks = 0, redup = 0.5 } = useContext(SceneContext);
  const g = GERAK[(indeks * 5 + 1) % GERAK.length];
  // zoom dramatis lebih kuat dari gaya lain
  const kamera = g.startsWith("zoom") || g === "naik" ? `scale(${Math.min(1.15 + frame * 0.0024, 1.75)})` : kameraTransform(g, frame);
  return (
    <AbsoluteFill style={{ background: theme.bg1 }}>
      <AbsoluteFill style={{ backgroundImage: noiseUri(7, 0.7, 0.45, "0.3 0.25 0.15"), opacity: 0.6, mixBlendMode: "multiply" }} />
      {gambarSrc ? (
        <Img
          src={staticFile(gambarSrc)}
          style={{ ...penuh, filter: "grayscale(1) contrast(1.7) brightness(0.92)", transform: kamera }}
        />
      ) : null}
      <AbsoluteFill style={{ background: `rgba(${theme.redupRgb},${gambarSrc ? redup : 0})` }} />
      <AbsoluteFill
        style={{
          backgroundImage: "radial-gradient(rgba(0,0,0,0.6) 1.3px, transparent 1.8px)",
          backgroundSize: "7px 7px",
          mixBlendMode: "multiply",
          opacity: 0.55,
        }}
      />
      <Isi>{children}</Isi>
    </AbsoluteFill>
  );
};

// ---------- 4. Clay: pastel bersih, gelembung lembut, kartu empuk memantul ----------
const LatarClay: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { gambarSrc, redup = 0.5 } = useContext(SceneContext);
  const s = spring({ frame, fps, config: { damping: 6, stiffness: 140 } });
  const napas = 1 + Math.sin(frame / 20) * 0.006;
  const gelembung = [
    { x: 40, y: 230, r: 150, c: theme.accent2 },
    { x: 800, y: 1500, r: 190, c: theme.accent },
    { x: 860, y: 260, r: 100, c: "#FFFFFF" },
    { x: 80, y: 1540, r: 120, c: theme.hijau },
  ];
  return (
    <AbsoluteFill style={{ background: theme.bg1 }}>
      {gelembung.map((b, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: b.x,
            top: b.y - Math.abs(Math.sin(frame / 18 + i)) * 34,
            width: b.r * 2,
            height: b.r * 2,
            borderRadius: "50%",
            background: `radial-gradient(circle at 30% 28%, rgba(255,255,255,0.85), ${b.c} 62%)`,
            boxShadow: "0 24px 40px rgba(70,50,140,0.22)",
            opacity: 0.95,
          }}
        />
      ))}
      {gambarSrc ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div
            style={{
              width: 940,
              height: 1360,
              borderRadius: 96,
              overflow: "hidden",
              border: "12px solid rgba(255,255,255,0.88)",
              boxShadow: "0 36px 70px rgba(70,50,140,0.3)",
              transform: `scale(${(0.7 + 0.3 * s) * napas})`,
              position: "relative",
            }}
          >
            <Img
              src={staticFile(gambarSrc)}
              style={{ ...penuh, transform: `scale(${Math.min(1.05 + frame * 0.0008, 1.3)})` }}
            />
            <AbsoluteFill style={{ background: `rgba(${theme.redupRgb},${redup})` }} />
          </div>
        </AbsoluteFill>
      ) : null}
      <Isi>{children}</Isi>
    </AbsoluteFill>
  );
};

export const Background: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  switch (theme.kode) {
    case "STYLE_PAPER_DAKWAH":
      return <LatarKertas>{children}</LatarKertas>;
    case "STYLE_RETRO_NOIR":
      return <LatarNoir>{children}</LatarNoir>;
    case "STYLE_CLAY_3D":
      return <LatarClay>{children}</LatarClay>;
    default:
      return <LatarHud>{children}</LatarHud>;
  }
};
