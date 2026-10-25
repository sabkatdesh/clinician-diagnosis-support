import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => {
  return {
    plugins: [react()],
    base: command === 'build' ? '/static/' : '/',
    resolve: {
      alias: { '@': '/src' },
    },
    build: {
      outDir: '.',
      emptyOutDir: false,
      rollupOptions: {
        output: {
          assetFileNames: 'assets/[name]-[hash][extname]',
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
        },
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/auth':     'http://localhost:8000',
        '/pipeline': 'http://localhost:8000',
        '/sessions': 'http://localhost:8000',
        '/patients': 'http://localhost:8000',
        '/health':   'http://localhost:8000',
      },
    },
  }
})
