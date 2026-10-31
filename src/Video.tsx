import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Series,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { SubtitleTengah } from "./components/Captions";
import { HudOverlay, NoirEfek } from "./components/Efek";
import { KataKunci } from "./components/KataKunci";
import { SceneContext } from "./components/SceneContext";
import { Sfx } from "./components/Sfx";
import { acak, poligonSobek } from "./components/tekstur";
import { renderScene } from "./scenes";
import { terapkanGaya, theme } from "./theme";
import type { VideoProps } from "./types";

// Scene yang menonjolkan ilustrasi (lapisan tipis); scene data lebih pekat agar teks terbaca.
const SCENE_GAMBAR = ["hook", "cerita", "pertanyaan", "fakta", "outro"];

// Transisi masuk khas tiap gaya (daftar ada di theme.masuk):
// HUD: glitch / scan / data wipe, Kertas: sobekan / ditempel, Noir: tinta / robekan / potong, Clay: pop.
const IsiScene: React.FC<{ indeks: number; children: React.ReactNode }> = ({
  indeks,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const jenis = theme.masuk[(indeks * 3 + 1) % theme.masuk.length];
  const p = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const s = spring({ frame, fps, config: { damping: 8, stiffness: 150 } });

  let gaya: React.CSSProperties = { opacity: p };
  switch (jenis) {
    case "glitch": {
      const aktif = frame < 9;
      const dx = aktif ? (acak(frame + indeks * 7) - 0.5) * 70 : 0;
      gaya = {
        transform: `translateX(${dx}px)`,
        opacity: aktif && frame % 2 === 0 ? 0.55 : 1,
        filter: aktif ? "contrast(1.3) saturate(1.2)" : undefined,
      };
      break;
    }
    case "scan":
      gaya = { clipPath: `inset(0 0 ${(1 - p) * 100}% 0)` };
      break;
    case "data":
      gaya = { clipPath: `inset(0 ${(1 - p) * 100}% 0 0)` };
      break;
    case "sobek":
      gaya = { clipPath: p >= 1 ? undefined : poligonSobek(p, indeks + 1, "x") };
      break;
    case "tempel":
      gaya = { opacity: Math.min(1, s * 2), transform: `scale(${0.8 + 0.2 * s})` };
      break;
    case "tinta":
      gaya = { clipPath: p >= 1 ? undefined : `circle(${p * 150}% at 50% 50%)` };
      break;
    case "robek":
      gaya = { clipPath: p >= 1 ? undefined : poligonSobek(p, indeks + 3, "y") };
      break;
    case "potong":
      gaya = { opacity: frame < 3 && frame % 2 === 0 ? 0.4 : 1 };
      break;
    case "pop":
      gaya = { opacity: Math.min(1, s * 2.5), transform: `scale(${0.6 + 0.4 * s})` };
      break;
    default:
      break;
  }
  return <AbsoluteFill style={gaya}>{children}</AbsoluteFill>;
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
        height: theme.kode === "STYLE_HUD_TECH" ? 4 : 10,
        width: `${(frame / durationInFrames) * 100}%`,
        background: theme.accent,
        borderRadius: 5,
      }}
    />
  );
};

export const MainVideo: React.FC<VideoProps> = ({ scenes, musikSrc, sfx, gaya, latar }) => {
  const { fps } = useVideoConfig();
  terapkanGaya(gaya, latar); // harus dipanggil sebelum komponen lain membaca warna dan font

  let awal = 0;
  return (
    <AbsoluteFill style={{ background: theme.bg1 }}>
      <Series>
        {scenes.map((scene, i) => {
          const frames = Math.max(1, Math.round(scene.durasi * fps));
          const mulai = awal;
          awal += frames;
          return (
            <Series.Sequence key={i} durationInFrames={frames}>
              <SceneContext.Provider
                value={{
                  gambarSrc: scene.gambarSrc,
                  indeks: i,
                  awal: mulai,
                  redup: SCENE_GAMBAR.includes(scene.type) ? 0.1 : 0.55,
                  sfx,
                }}
              >
                <IsiScene indeks={i}>{renderScene(scene)}</IsiScene>
                {/* scene data/grafik sudah menampilkan teks sendiri, jadi subtitle hanya untuk scene cerita */}
                {scene.type === "cerita" ? <SubtitleTengah kata={scene.kata} /> : null}
                {scene.type === "cerita" ? (
                  <KataKunci kunci={scene.kunci} stiker={scene.stiker} />
                ) : null}
                {theme.kode === "STYLE_HUD_TECH" ? <HudOverlay label={scene.label} /> : null}
                {theme.kode === "STYLE_RETRO_NOIR" ? <NoirEfek /> : null}
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
