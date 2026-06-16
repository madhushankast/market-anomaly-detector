import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      usePolling: true, // Forces Vite to manually check for file saves inside Docker
    },
    host: true, // Allows the server to be exposed outside the container
    port: 5173,
  },
})