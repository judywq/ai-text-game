import { fileURLToPath, URL } from 'node:url'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { extname, normalize, relative, resolve as resolvePath } from 'node:path'
import { defineConfig, type Connect, type Plugin, type PreviewServer, type ViteDevServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import autoprefixer from 'autoprefixer'
import tailwind from 'tailwindcss'
import pkg from './package.json'

const mockupPerspectiveDir = fileURLToPath(
  new URL('./src/assets/ui-concepts/mockup-perspective', import.meta.url),
)

const mimeTypes: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
}

function serveMockupPerspective(): Plugin {
  const handler: Connect.NextHandleFunction = (req, res, next) => {
    const url = req.url?.split('?')[0] ?? ''
    if (!url.startsWith('/mockup-perspective')) return next()

    const requested = decodeURIComponent(url.replace(/^\/mockup-perspective\/?/, '') || 'index.html')
    const filePath = resolvePath(mockupPerspectiveDir, requested)
    const relativePath = relative(mockupPerspectiveDir, filePath)
    if (relativePath.startsWith('..') || normalize(relativePath) !== relativePath) {
      res.statusCode = 403
      res.end('Forbidden')
      return
    }
    if (!existsSync(filePath) || !statSync(filePath).isFile()) return next()

    res.setHeader('Content-Type', mimeTypes[extname(filePath).toLowerCase()] || 'application/octet-stream')
    createReadStream(filePath).pipe(res)
  }

  const mount = (server: ViteDevServer | PreviewServer) => {
    server.middlewares.use(handler)
  }

  return {
    name: 'serve-mockup-perspective',
    configureServer: mount,
    configurePreviewServer: mount,
  }
}

// https://vite.dev/config/
export default defineConfig({
  server: {
    watch: {
      usePolling: true,
    },
  },
  css: {
    postcss: {
      plugins: [tailwind(), autoprefixer()],
    },
  },
  plugins: [
    vue(),
    vueDevTools(),
    serveMockupPerspective(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version)
  }
})
