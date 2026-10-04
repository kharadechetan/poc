import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/machines': 'http://127.0.0.1:8000',
      '/work-orders': 'http://127.0.0.1:8000',
      '/schedule': 'http://127.0.0.1:8000',
      '/simulation': 'http://127.0.0.1:8000',
    }
  }
})
