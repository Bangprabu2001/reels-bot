import React from "react";
import {
  AbsoluteFill,
  Audio,
  Series,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { SubtitleTengah } from "./components/Captions";
import { SceneContext } from "./components/SceneContext";
import { Sfx } from "./components/Sfx";
import { renderScene } from "./scenes";
import { terapkanTema, theme } from "./theme";
import type { VideoProps } from "./types";

// Scene yang menonjolkan ilustrasi (lapisan gelap tipis); scene data lebih gelap agar teks terbaca.
const SCENE_GAMBAR = ["hook", "cerita", "fakta", "outro"];

// Fade-in singkat di awal tiap scene.
const IsiScene: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const masuk = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: masuk }}>{children}</AbsoluteFill>;
};

// Bilah kemajuan tipis di atas: trik umum untuk menjaga penonton sampai akhir.
const BilahKemajuan: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        top: 128,
        height: 10,
        width: `${(frame / durationInFrames) * 100}%`,
        background: theme.accent,
        borderRadius: 5,
      }}
    />
  );
};

export const MainVideo: React.FC<VideoProps> = ({ scenes, musikSrc, sfx, tema }) => {
  const { fps } = useVideoConfig();
  terapkanTema(tema); // harus dipanggil sebelum komponen lain membaca warna

  return (
    <AbsoluteFill style={{ background: theme.bg1 }}>
      <Series>
        {scenes.map((scene, i) => {
          const frames = Math.max(1, Math.round(scene.durasi * fps));
          return (
            <Series.Sequence key={i} durationInFrames={frames}>
              <SceneContext.Provider
                value={{
                  gambarSrc: scene.gambarSrc,
                  brollSrc: scene.brollSrc,
                  indeks: i,
                  redup: SCENE_GAMBAR.includes(scene.type) ? 0.1 : 0.55,
                  sfx,
                }}
              >
                <IsiScene>{renderScene(scene)}</IsiScene>
                {/* scene data/grafik sudah menampilkan teks sendiri, jadi subtitle hanya untuk scene cerita */}
                {scene.type === "cerita" ? <SubtitleTengah kata={scene.kata} /> : null}
                <Sfx nama="whoosh" volume={0.22} />
              </SceneContext.Provider>
              {scene.audioSrc ? <Audio src={staticFile(scene.audioSrc)} /> : null}
            </Series.Sequence>
          );
        })}
      </Series>
      <BilahKemajuan />
      {musikSrc ? <Audio src={staticFile(musikSrc)} volume={0.14} loop /> : null}
    </AbsoluteFill>
  );
};
