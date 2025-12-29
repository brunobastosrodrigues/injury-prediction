import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    define: {
      global: 'globalThis',
    },
    server: {
      host: true,
      proxy: {
        '/api': {
          target: env.BACKEND_URL || 'http://localhost:5000',
          changeOrigin: true
        }
      }
    }
  }
})
