# Project notes for Claude

## Where changes go

Production is the only copy: commit to `main` in this repo. CI runs, then Vercel deploys to https://ftaguild.com.
(The old claude.ai artifact was retired on 2026-11-13; don't republish to it.)

## Before pushing

Run `npm run check` (HTML validation + file/link/size check). CI runs the same thing.

## Where things are

- Guild details (Discord link, officers, weekly schedule): the `GUILD` object in `public/index.html`
- Intro layers: `tools/intro/make_layers.py`; guild theme: `tools/music/compose.py`

## SEO

Title, description, keywords, canonical, Open Graph/Twitter tags and JSON-LD live in the `<head>` of `public/index.html`.
Social preview image: `public/og-image.jpg` (1200x630). Icons: `favicon.ico`, `favicon-32.png`, `apple-touch-icon.png`, `icon-192/512.png`.
Update `public/sitemap.xml` `lastmod` when content changes meaningfully.
