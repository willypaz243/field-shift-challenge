import type { ImageSourcePropType } from "react-native";
import index from "../../../data/gamc/04/zonas/index.json";
import { gamcImages } from "./gamc-images";

export type GamcMap = {
  bbox: number[];
  image: ImageSourcePropType;
};

type Entry = { bbox: number[]; width: number; height: number };

export function gamcMap(zoneId: string): GamcMap | null {
  const entry = (index.zonas as Record<string, Entry>)[zoneId];
  const image = gamcImages[zoneId];
  return entry && image ? { bbox: entry.bbox, image } : null;
}
