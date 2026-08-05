import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import Sitemap from 'vite-plugin-sitemap'

// https://vite.dev/config/
export default defineConfig({
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
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
