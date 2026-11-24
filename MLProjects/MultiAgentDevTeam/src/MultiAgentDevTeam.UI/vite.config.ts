import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `npm run dev` serves on 3000 and proxies /api to the Orchestrator on 5000 (the Docker stack).
// `npm run dev:debug` serves on 3001 and proxies to 5002, the Orchestrator started from
// Visual Studio, so both can run side by side. API_PROXY_TARGET overrides either target.
export default defineConfig(({ mode }) => {
  const debug = mode === 'debug'
  return {
    plugins: [react()],
    server: {
      port: debug ? 3001 : 3000,
      strictPort: debug,
      proxy: {
        '/api': {
          target: process.env.API_PROXY_TARGET ?? (debug ? 'http://localhost:5002' : 'http://localhost:5000'),
          changeOrigin: true
        }
      }
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test-setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
      exclude: ['e2e/**', 'node_modules/**'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html'],
        thresholds: { lines: 80, branches: 80 }
      }
    }
  }
})
