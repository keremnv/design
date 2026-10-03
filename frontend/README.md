# Ontology Author inspector

This directory contains the source for the bundled, read-only World inspector.
It is built into `ontology_author/world/static/` and served by `author open`.

## Run

Build from this directory:

```bash
npm install
npm run build
```

For development, `npm run dev` serves the inspector and proxies `/world` to a
local World API. The normal user path is `author open [world]`, which requires
no frontend installation.

The [visibility design](VISIBILITY.md) explains how names yield to crowding
while preserving the inspector's material and motion language.

## Browser regression tests

The tests run the real inspector with fixture API responses, including delayed
and failed reads. They do not construct or mutate a World.

```bash
npm ci
npx playwright install chromium
npm test
```

To use an existing Chrome/Chromium installation, set
`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to its executable path instead of
downloading Chromium. The test runner starts and stops its own Vite server.
