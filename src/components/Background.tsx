import React, { useContext } from "react";
import { AbsoluteFill, Img, OffthreadVideo, staticFile, useCurrentFrame } from "remotion";
import { theme } from "../theme";
import { SceneContext } from "./SceneContext";

// Partikel kecil bercahaya yang melayang pelan: memberi kesan hidup pada gambar diam.
const Debu: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: 16 }, (_, i) => {
        const x = (i * 137) % 1080;
        const naik = (frame * (0.6 + (i % 5) * 0.25) + i * 211) % 2100;
        const ukuran = 6 + (i % 4) * 4;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + Math.sin(frame / 40 + i) * 30,
              top: 2000 - naik,
              width: ukuran,
              height: ukuran,
              borderRadius: "50%",
              background: i % 2 ? theme.accent : theme.accent2,
              opacity: 0.35,
              boxShadow: `0 0 ${ukuran * 2}px ${i % 2 ? theme.accent : theme.accent2}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const Background: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const frame = useCurrentFrame();
  const { top, bottom, side } = theme.safe;
  const { gambarSrc, brollSrc, indeks = 0, redup = 0.5 } = useContext(SceneContext);

  // Gerak kamera pelan (Ken Burns): zoom perlahan + geser, arahnya berganti tiap scene.
  const arah = indeks % 2 === 0 ? 1 : -1;
  const zoom = Math.min(1.1 + frame * 0.0009, 1.45);
  const geserX = arah * frame * 0.14;
  const geserY = -frame * 0.07;
  const kamera = `scale(${zoom}) translate(${geserX}px, ${geserY}px)`;

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${150 + Math.sin(frame / 90) * 12}deg, ${theme.bg1}, ${theme.bg2})`,
        overflow: "hidden",
      }}
    >
      {gambarSrc ? (
        <>
          <Img
            src={staticFile(gambarSrc)}
            style={{ width: "100%", height: "100%", objectFit: "cover", transform: kamera }}
          />
          {/* lapisan gelap: tipis untuk scene bercerita, tebal untuk scene data */}
          <AbsoluteFill style={{ background: `rgba(7,9,15,${redup})` }} />
          <AbsoluteFill
            style={{
              background:
                "linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 78%, rgba(0,0,0,0.55) 100%)",
            }}
          />
        </>
      ) : brollSrc ? (
        <>
          <OffthreadVideo
            src={staticFile(brollSrc)}
            volume={0}
            style={{ width: "100%", height: "100%", objectFit: "cover", transform: kamera }}
          />
          <AbsoluteFill style={{ background: "rgba(7,9,15,0.6)" }} />
        </>
      ) : (
        [0, 1, 2].map((i) => (
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
        ))
      )}
      <Debu />
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
