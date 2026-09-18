import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const webRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  root: resolve(webRoot, "static-preview"),
  base: "/ECC-Buildings/",
  publicDir: resolve(webRoot, "public"),
  resolve: { alias: { "@": webRoot } },
  css: { postcss: webRoot },
  plugins: [react()],
  build: {
    outDir: resolve(webRoot, "pages-dist"),
    emptyOutDir: true,
  },
});
