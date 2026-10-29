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
import { BawahLayar } from "./components/Captions";
import { SceneContext } from "./components/SceneContext";
import { renderScene } from "./scenes";
import { theme } from "./theme";
import type { VideoProps } from "./types";

// Fade-in singkat di awal tiap scene + zoom pelan pada isi scene (kesan kamera bergerak).
const IsiScene: React.FC<{ frames: number; children: React.ReactNode }> = ({
  frames,
  children,
}) => {
  const frame = useCurrentFrame();
  const masuk = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const zoom = interpolate(frame, [0, frames], [1, 1.05]);
  return (
    <AbsoluteFill style={{ opacity: masuk, transform: `scale(${zoom})` }}>
      {children}
    </AbsoluteFill>
  );
};

export const MainVideo: React.FC<VideoProps> = ({ scenes, musikSrc }) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ background: theme.bg1 }}>
      <Series>
        {scenes.map((scene, i) => {
          const frames = Math.max(1, Math.round(scene.durasi * fps));
          return (
            <Series.Sequence key={i} durationInFrames={frames}>
              <SceneContext.Provider value={{ brollSrc: scene.brollSrc }}>
                <IsiScene frames={frames}>{renderScene(scene)}</IsiScene>
                <BawahLayar
                  kata={scene.kata}
                  ekspresi={scene.ekspresi}
                  caption={scene.type !== "hook" && scene.type !== "outro"}
                />
              </SceneContext.Provider>
              {scene.audioSrc ? <Audio src={staticFile(scene.audioSrc)} /> : null}
            </Series.Sequence>
          );
        })}
      </Series>
      {musikSrc ? <Audio src={staticFile(musikSrc)} volume={0.12} loop /> : null}
    </AbsoluteFill>
  );
};
