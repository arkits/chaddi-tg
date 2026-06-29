import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const API_BASE_URL = process.env.VITE_API_BASE_URL || "http://localhost:5100";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: API_BASE_URL,
        changeOrigin: true,
      },
      "/socket.io": {
        target: API_BASE_URL,
        ws: true,
      },
    },
  },
});
