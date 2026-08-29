import { defineConfig } from 'vitest/config'
import { loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import Sitemap from 'vite-plugin-sitemap'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
  plugins: [
    react(),
    Sitemap({
      hostname: 'https://fungus-mcp.dev', // Replace with actual hostname
      dynamicRoutes: [
        '/',
        '/docs',
        '/dashboard'
      ],
      generateRobotsTxt: true
    })
  ],
  // Dev proxy: adds X-API-Key server-side so the key never reaches the browser
  server: {
    proxy: {
      '/api': {
        target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
        headers: {
          'X-API-Key': env.FUNGUS_API_KEY || '',
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
}
})
