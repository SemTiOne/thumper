import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During UI-first development the backend is mocked in-browser (src/api).
// When the real FastAPI server exists, point the proxy at it and swap the
// mock client for the http client in src/api/index.ts.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
