import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/components'),
      '@pages':      resolve(__dirname, './src/pages'),
      '@services':   resolve(__dirname, './src/services'),
      '@hooks':      resolve(__dirname, './src/hooks'),
      '@context':    resolve(__dirname, './src/context'),
      '@utils':      resolve(__dirname, './src/utils'),
      '@layouts':    resolve(__dirname, './src/layouts'),
    },
  },
  server: {
    port: 3001,
    open: true,
  },
})
