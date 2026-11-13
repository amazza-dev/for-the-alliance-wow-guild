# Project notes for Claude

## Two places to update on every change

This site lives in two places. **Every change must go to both:**

1. **GitHub → Vercel (production):** commit to `main` in this repo. CI runs, then Vercel deploys to https://for-the-alliance-wow-guild.vercel.app
2. **claude.ai artifact:** republish the changed files from `public/` to the artifact
   `https://claude.ai/artifact/LNGtNLX8XuNaAEYf1rbmYq` (slug `9cd60b28-cc16-4427-be9a-4617afeb98c6`).
   The artifact is shared publicly, so republish with `shared_live: "public"`.

## Before pushing

Run `npm run check` (HTML validation + file/link/size check). CI runs the same thing.

## Where things are

- Guild details (Discord link, officers, weekly schedule): the `GUILD` object in `public/index.html`
- Intro layers: `tools/intro/make_layers.py`; guild theme: `tools/music/compose.py`
