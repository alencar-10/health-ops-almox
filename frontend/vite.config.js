import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Portas oficiais: docs/OFFICIAL_LOCAL_PORTS.md
export default defineConfig({
  plugins: [react()],
  server: {
    // IPv4 + IPv6: evita recusar ligação em 127.0.0.1 quando só ::1 está a escutar
    host: true,
    port: 5173,
    proxy: {
      '/almox': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
