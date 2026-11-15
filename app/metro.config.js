const path = require("path");
const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);
// The offline mock imports the shared crop catalog from the repo root.
config.watchFolders = [path.resolve(__dirname, "../data/crops")];
// expo-sqlite on web ships its SQLite engine as a .wasm asset.
config.resolver.assetExts.push("wasm");

module.exports = config;
