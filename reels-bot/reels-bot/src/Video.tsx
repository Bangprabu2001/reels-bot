import React from "react";
import { AbsoluteFill, Audio, Series, staticFile, useVideoConfig } from "remotion";
import { Captions } from "./components/Captions";
import { renderScene } from "./scenes";
import type { VideoProps } from "./types";

export const MainVideo: React.FC<VideoProps> = ({ scenes, musikSrc }) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      <Series>
        {scenes.map((scene, i) => (
          <Series.Sequence
            key={i}
            durationInFrames={Math.max(1, Math.round(scene.durasi * fps))}
          >
            {renderScene(scene)}
            {/* Hook sudah menampilkan teks besar, jadi tanpa subtitle */}
            {scene.type !== "hook" ? <Captions kata={scene.kata} /> : null}
            {scene.audioSrc ? <Audio src={staticFile(scene.audioSrc)} /> : null}
          </Series.Sequence>
        ))}
      </Series>
      {musikSrc ? <Audio src={staticFile(musikSrc)} volume={0.12} loop /> : null}
    </AbsoluteFill>
  );
};
