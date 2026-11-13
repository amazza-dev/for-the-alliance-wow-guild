# For the Alliance — WoW guild website

[![CI](https://github.com/amazza-dev/for-the-alliance-wow-guild/actions/workflows/ci.yml/badge.svg)](https://github.com/amazza-dev/for-the-alliance-wow-guild/actions/workflows/ci.yml)

The website for **For the Alliance**, a friendly, semi-competitive World of Warcraft guild on **WoW Forever (PvP)**. Raiding, PvP events, and leveling help.

Live at **https://ftaguild.com**. It's a static site: one `index.html` plus images and music, no build step.

- Animated intro: the guild banner assembles itself (shield, lion rising and roaring, title, ribbon, weapons), then **Enter the realm** starts the guild theme.
- Weekly schedule, raid info, guild code, officers, FAQ.
- Application form that formats an application for members to paste into Discord.

## Run it locally

```bash
npm install
npm run dev        # serves public/ at http://localhost:3000
```

## Edit guild details

Everything that changes week to week lives in the `GUILD` object near the top of the script in `public/index.html`:

- `discordUrl`: the Discord invite
- `officers`: names, roles and badge colors
- `schedule`: events by day (`0` = Sunday … `6` = Saturday), with type `raid`, `pvp`, `level` or `social`

## Checks (CI)

Every push and pull request to `main` runs `.github/workflows/ci.yml`:

1. **HTML validation** with [html-validate](https://html-validate.org) (`npm run validate`)
2. **Site check** (`npm run check:assets`): every file the page references exists, every `#link` has a target, and no asset is over 3 MB

Run both locally with `npm run check`.

## Deploys (CD)

Hosted on Vercel at **https://ftaguild.com** (`www.` and the old `for-the-alliance-wow-guild.vercel.app` address both redirect there). `vercel.json` serves `public/` with no build.

- Push to `main` → production deploy
- Open a pull request → preview deploy with its own URL

## Project layout

```
public/            the site (deployed as-is)
assets-src/        original banner artwork
tools/intro/       make_layers.py: cuts the banner into the intro animation layers
tools/music/       compose.py: synthesizes the guild theme (original, no samples)
scripts/           check-site.mjs: the CI site check
```

### Rebuilding the intro layers or the music

Both tools need Python 3 with `numpy`, `scipy` and `Pillow`, and the music needs `ffmpeg`.

```bash
python3 tools/intro/make_layers.py     # rewrites the .webp layers, full.jpg and banners in public/
python3 tools/music/compose.py         # writes tools/music/theme.wav; see the script header for the ffmpeg master step
```

If you change the layer cut-outs, `make_layers.py` prints each layer's position; copy those into the matching `<img>` styles in `index.html`.

---

Fan-run guild site. Not affiliated with or endorsed by Blizzard Entertainment. The guild theme is an original composition.
