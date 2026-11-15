const path = require("path");
const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);
// The offline mock imports the shared crop catalog from the repo root, and the
// zone maps import the GAMC base images.
config.watchFolders = [
  path.resolve(__dirname, "../data/crops"),
  // GAMC base maps per zone, precomputed by src/etl/gamc_zone_maps.py.
  path.resolve(__dirname, "../data/gamc/04/zonas"),
];
// expo-sqlite on web ships its SQLite engine as a .wasm asset.
config.resolver.assetExts.push("wasm");

module.exports = config;
