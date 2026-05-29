import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 代理 BMN 后端
      '/api': {
        target: 'http://127.0.0.1:5003',
        changeOrigin: true,
      },
      // 代理原 AIAdPlacer 后端（如需）
      '/api/v1': {
        target: 'http://127.0.0.1:5002',
        changeOrigin: true,
      },
      '/api/v2': {
        target: 'http://127.0.0.1:5002',
        changeOrigin: true,
      },
    },
  },
})
