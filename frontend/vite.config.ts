import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    // plotly.js-dist-min is a single prebuilt ~4 MB bundle (see plot.ts) --
    // it's lazy-loaded on its own chunk (only the Response Analysis page
    // needs it) but can't be split down further, so raise the warning
    // threshold rather than let it fire on every build.
    chunkSizeWarningLimit: 4500,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
  },
})
