// Serves the exported web build (`npx expo export --platform web`) for testing
// in a browser. expo-sqlite on web needs SharedArrayBuffer, which browsers only
// allow on cross-origin isolated pages, and the Expo dev server does not send
// these headers on the HTML page.
import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";

const root = join(import.meta.dirname, "..", "dist");
const port = Number(process.env.PORT ?? 8081);
const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".wasm": "application/wasm",
  ".png": "image/png",
  ".webp": "image/webp",
  ".ttf": "font/ttf",
  ".ico": "image/x-icon",
};

createServer((req, res) => {
  const path = normalize(decodeURIComponent(new URL(req.url, "http://x").pathname));
  let file = join(root, path);
  if (!file.startsWith(root)) {
    res.writeHead(403).end();
    return;
  }
  if (existsSync(file) && statSync(file).isDirectory()) file = join(file, "index.html");
  if (!existsSync(file) && existsSync(`${file}.html`)) file = `${file}.html`;
  // Client-side routes (expo-router) fall back to the app shell.
  if (!existsSync(file)) file = join(root, "index.html");
  res.writeHead(200, {
    "Content-Type": types[extname(file)] ?? "application/octet-stream",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
  });
  createReadStream(file).pipe(res);
}).listen(port, () => console.log(`Choclito web: http://localhost:${port}`));
