// Restores the Vite dev entry index.html after a production build.
// `npm run build` (outDir: '.') overwrites index.html with the hashed-asset
// production version. This script writes back the dev template so that
// `npm run dev` works again immediately after building.
const fs = require('fs')
const path = require('path')

const devHtml = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#0f766e" />
    <title>Clinical AI — Decision Support</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
`

const dest = path.join(__dirname, '..', 'index.html')
fs.writeFileSync(dest, devHtml, 'utf8')
console.log('✓ Restored dev index.html')
