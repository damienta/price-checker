import fs from 'node:fs'
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

const DATA_DIR = path.resolve(import.meta.dirname, '../data')

/** In dev, serve the repo's data/ folder at /data so the site shows your local files. */
function localData(): Plugin {
  return {
    name: 'local-data',
    configureServer(server) {
      server.middlewares.use('/data', (req, res, next) => {
        const file = path.join(DATA_DIR, path.basename((req.url ?? '').split('?')[0]))
        if (!file.startsWith(DATA_DIR) || !fs.existsSync(file)) return next()
        res.setHeader('Content-Type', file.endsWith('.csv') ? 'text/csv' : 'application/json')
        fs.createReadStream(file).pipe(res)
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  // GitHub Pages serves the site from /price-checker/.
  base: process.env.GITHUB_PAGES ? '/price-checker/' : '/',
  plugins: [react(), tailwindcss(), localData()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'react', test: /node_modules[\/](react|react-dom|scheduler)[\/]/ },
            { name: 'motion', test: /node_modules[\/](framer-motion|motion-dom|motion-utils)[\/]/ },
          ],
        },
      },
    },
  },
})
