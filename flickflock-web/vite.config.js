import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': {
           target: 'https://flickflock-backend-vr3q5dt6va-ew.a.run.app/api',
           changeOrigin: true,
           secure: false,
           ws: true,
           rewrite: (path) => path.replace(/^\/api/, "")
       }
    }
  }
})
