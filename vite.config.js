import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'src/dist',   // ← ahora el build cae dentro de /src/dist
    assetsDir: 'assets',
    emptyOutDir: true,
  },
})