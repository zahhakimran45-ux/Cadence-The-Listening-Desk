# Cadence — Music, decoded

An Apple Music-inspired song analysis & discovery app. Type a song name and get its **sonic DNA**, nearest relatives, mood discovery, a generated mixtape, and a shareable card — now with **Liquid Glass**, a full **Library**, and an **Adaptive engine** that learns your taste.

## Run

```bash
cd cadence
python3 server.py
# open http://localhost:8000
```

Python 3.9+ only, no deps. `server.py` serves the app + proxies live lookups (iTunes → Deezer fallback) and audio previews. Or just open `index.html` standalone (offline, 220 songs inlined).

## What's inside

| Feature | How it works |
|---|---|
| **Sonic DNA** | Five editorial dimensions (Energy, Danceability, Warmth, Acousticness, Instrumental) + BPM/Key/Duration/Loudness. Radar + bars. |
| **Deep scan audio** | Downloads a 30s preview via the local proxy, decodes with **Web Audio API** in your browser, measures RMS, crest factor, brightness, bass weight, stereo width + tempo via onset autocorrelation. Nothing uploaded. |
| **Nearest relatives** | Weighted L1 distance over the five dimensions + tempo/era/genre. Six modes: Closest / Calmer / More energy / Same era / Same genre / Wildcard, with a plain-English reason. |
| **Moods & Dials** | Eight preset scenes + three live dials that re-rank the whole catalog. |
| **Mixtape** | 12-track arc: Arrive → Rise → Peak → Fall → Land. Export as `.m3u`, `.json`, text or YouTube Music searches. |
| **Song Card** | 900×1200 canvas poster with fingerprint + top 3 relatives. PNG or text. |
| **Live lookup** | If a title isn't on the 220-song shelf, `/api/search` pulls from iTunes/Deezer and builds a metadata-based estimate (labelled). |

### New in this release

**Library** — sidebar → Library (and `Library` tab on mobile). Every heart/save lands here. Grid with cover, title, artist, genre/year/length, **Play** (30s preview) and **Analyze** per card, remove (`×`), filter-as-you-type, sort (Recent / Title / Artist / Year), `Clear all`, and **Play all as mixtape** (builds a mixtape from your collection + taste fills). Stats bar shows Favorites / Hours / Top genre. Empty state guides you.

**Liquid Glass** — iOS 26 / Apple Music glass over *every* surface: translucent `backdrop-filter: blur(22–28px) saturate(165–180%)` chrome for sidebar / top bar / player, glass cards for hero, song head, radar, bars, stats, match list, mood tiles, dial box, tape list/side, how-it-works cards, library grid and toasts. Living gradient blobs behind the page, specular top-edge highlights and soft outer shadows. Respects light/dark themes.

**Adaptive engine** — learns locally in `localStorage` (`cadence.taste`). Every **analyze = 1, play = 1.5, save = 3** signal updates a weighted taste vector (5 DNA dims + BPM + year + genre histogram). Home page **"Made for you"** block appears immediately (random discovery before learning) and after 2–3 signals becomes personal: a tiny taste radar, `X signals` badge, top-genre pills and an 8-track **For you** shelf (`p% for you`) that re-ranks the whole catalog by distance to your taste. Library also shows *What Cadence learned* with the same radar and pills. Refreshes on each interaction and on tab focus; persists across reloads.

## Files

```
index.html          ← built, self-contained deliverable
server.py           ← static + API: /api/search, /api/preview, /api/audio, /api/health
build.py            ← bundles src/ → index.html
build_catalog.py    ← source of the 220-song dataset
src/template.html
src/styles.css      ← Apple Music + Liquid Glass system
src/app.js          ← analysis, similarity, player, adaptive, library
src/catalog.json    ← generated data (58k)
```

After editing `src/` or `build_catalog.py`:

```bash
python3 build_catalog.py   # if dataset changed
python3 build.py
```

Adding a song → append to `RAW` in `build_catalog.py`:

```
Title|Artist|Year|Genre|BPM|DurationSeconds|E|D|V|A|I   # E,D,V,A,I in 0..1
```

## Notes

Catalog DNA values are editorial estimates for legibility; measured figures come only from Deep Scan (30s excerpt) or from live-search genre/year estimates.

## Deploy to Vercel (make it live)

Your project is now **Vercel-ready** — `index.html` + `api/` serverless functions + `vercel.json` are all included. No extra setup.

### Easiest — Dashboard (no terminal)

1. Push this `cadence` folder to GitHub (drag & drop on github.com/new)
2. Go to **vercel.com/new** → `Import Git Repository` → pick `cadence`
3. Click **Deploy** (leave all defaults, Framework: Other)
4. Done! Your live link: `https://your-project.vercel.app` — works on Android/iPhone instantly. `Add to Home Screen` for an app icon.

### Via CLI (1 command)

```bash
npm i -g vercel
vercel login          # opens browser to authorize
cd cadence
vercel                # preview deploy
vercel --prod         # production deploy → live URL
```

### What Vercel runs

- `index.html` → static site (Liquid Glass + Library + Adaptive)
- `api/search.py` → `GET /api/search?q=...` (iTunes → Deezer fallback)
- `api/preview.py` → `GET /api/preview?q=...` (MP3-first preview picker)
- `api/audio.py` → `GET /api/audio?url=...` (proxy so Web Audio can decode)
- `api/health.py` → `GET /api/health`

All Python stdlib only — no `requirements` needed. Subsequent pushes to GitHub auto-redeploy.
