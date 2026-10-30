import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { MainVideo } from "./Video";
import type { VideoProps } from "./types";
import example from "../data/example.json";

const FPS = 30;

// Durasi total mengikuti jumlah durasi semua scene di JSON.
const calculateMetadata: CalculateMetadataFunction<VideoProps> = ({ props }) => ({
  durationInFrames: Math.max(
    1,
    Math.round(props.scenes.reduce((a, s) => a + s.durasi, 0) * FPS),
  ),
});

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reels"
    component={MainVideo}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={FPS * 16}
    defaultProps={example as unknown as VideoProps}
    calculateMetadata={calculateMetadata}
  />
);
