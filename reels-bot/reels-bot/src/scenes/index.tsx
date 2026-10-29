import React from "react";
import type { Scene } from "../types";
import { HookScene } from "./HookScene";
import { BarChartScene } from "./BarChartScene";
import { ListScene } from "./ListScene";

// Tambah template baru: buat komponennya, tambah tipenya di types.ts, lalu daftarkan di sini.
export const renderScene = (scene: Scene): React.ReactElement => {
  switch (scene.type) {
    case "hook":
      return <HookScene scene={scene} />;
    case "bar_chart":
      return <BarChartScene scene={scene} />;
    case "list":
      return <ListScene scene={scene} />;
  }
};
