import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The API runs separately in development (uvicorn on 8080); in production FastAPI
// serves this build from the same origin, so no CORS either way.
const api = "http://127.0.0.1:8080";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/predict": api, "/api": api, "/health": api },
  },
  build: {
    outDir: "dist",
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, "index.html"),
        stats: resolve(import.meta.dirname, "stats/index.html"),
      },
    },
  },
});
