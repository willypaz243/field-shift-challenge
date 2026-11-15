import type { ImageSourcePropType } from "react-native";
import papa from "../../assets/crops/papa.webp";
import choclo from "../../assets/crops/choclo.webp";
import trigo from "../../assets/crops/trigo.webp";
import papaliza from "../../assets/crops/papaliza.webp";
import lechuga from "../../assets/crops/lechuga.webp";
import hortalizas from "../../assets/crops/hortalizas.webp";
import alfalfa from "../../assets/crops/alfalfa.webp";
import haba from "../../assets/crops/haba.webp";
import tarwi from "../../assets/crops/tarwi.webp";
import quinua from "../../assets/crops/quinua.webp";
import avena from "../../assets/crops/avena.webp";
import durazno from "../../assets/crops/durazno.webp";
import flores from "../../assets/crops/flores.webp";
import maiz_forraje from "../../assets/crops/maiz_forraje.webp";

// Imported one by one so Metro bundles every photo (credits in assets/crops/CREDITS.md).
export const cropImages: Record<string, ImageSourcePropType> = {
  papa,
  choclo,
  trigo,
  papaliza,
  lechuga,
  hortalizas,
  alfalfa,
  haba,
  tarwi,
  quinua,
  avena,
  durazno,
  flores,
  maiz_forraje,
};
