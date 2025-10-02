import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: '.',
  build: {
    outDir: 'dist',      // <-- dist en la RAÍZ del repo
    assetsDir: 'assets',
    emptyOutDir: true,
  },
})