import React from "react";
import type { Scene } from "../types";
import { HookScene } from "./HookScene";
import { CeritaScene } from "./CeritaScene";
import { BarChartScene } from "./BarChartScene";
import { ListScene } from "./ListScene";
import { BigNumberScene } from "./BigNumberScene";
import { CompareScene } from "./CompareScene";
import { TimelineScene } from "./TimelineScene";
import { FaktaScene } from "./FaktaScene";
import { MitosFaktaScene } from "./MitosFaktaScene";
import { OutroScene } from "./OutroScene";

// Tambah template baru: buat komponennya, tambah tipenya di types.ts, daftarkan di sini
// dan di SKEMA pada scripts/pipeline.py.
export const renderScene = (scene: Scene): React.ReactElement => {
  switch (scene.type) {
    case "hook":
      return <HookScene scene={scene} />;
    case "cerita":
      return <CeritaScene scene={scene} />;
    case "bar_chart":
      return <BarChartScene scene={scene} />;
    case "list":
      return <ListScene scene={scene} />;
    case "big_number":
      return <BigNumberScene scene={scene} />;
    case "compare":
      return <CompareScene scene={scene} />;
    case "timeline":
      return <TimelineScene scene={scene} />;
    case "fakta":
      return <FaktaScene scene={scene} />;
    case "mitos_fakta":
      return <MitosFaktaScene scene={scene} />;
    case "outro":
      return <OutroScene scene={scene} />;
  }
};
