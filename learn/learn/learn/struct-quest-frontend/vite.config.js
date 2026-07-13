import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      // 支持运行时模板编译（用于内联 template 字符串的子组件）
      'vue': 'vue/dist/vue.esm-bundler.js',
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://localhost:8008',
        ws: true,
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
    },
  },
})
