import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/register": "http://localhost:8000",
      "/login": "http://localhost:8000",
      "/users": "http://localhost:8000",
      "/chat": "http://localhost:8000"
    }
  }
});
