import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    // ⚡ CRÍTICO: exponer en red local (acceso por IP desde el jurado)
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // Redirige /api/* al backend Flask en desarrollo
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },

  preview: {
    // Para "npm run preview" (build de producción)
    host: '0.0.0.0',
    port: 4173,
  },

  build: {
    outDir: 'dist',
    // El backend Flask puede servir estos archivos estáticos
    assetsDir: 'assets',
  },
})
