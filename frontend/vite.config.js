import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/optimizer': 'http://127.0.0.1:8000',
      '/interview': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/github': 'http://127.0.0.1:8000',
    },
  },
})
