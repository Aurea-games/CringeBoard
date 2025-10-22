import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Minimal Vite config; plugins left empty to keep deps small.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
  },
})

