# POTA Alert

A small, single-page web app for chasing and planning
[POTA](https://pota.app) activations. Zero build tools, zero non-stdlib
dependencies — a tiny Python server plus one HTML file.

The UI has two tabs:

- **Hunter** — a live spot feed that pings you when a new activator comes
  on the air.
- **Activator** — a park browser with a state picker, search, and an
  optional radius filter around your QTH.

## Hunter tab

- Polls `https://api.pota.app/spot/activator` every 60 seconds.
- Shows every active activator in a live table, sorted by frequency
  ascending and grouped under band headers (160m → 70cm).
- Deduplicates by callsign (not per spot), so a chatty spotter doesn't
  flood you with notifications.
- Fires a browser notification the first time each callsign appears today.
  Click a row (or the **Mark all seen** button) to clear the 🆕 flag.
- Resets the "seen today" set at UTC midnight.
- **QRT detection** — if a spot's comment contains `qrt` as a whole word
  (`qrt`, `QRT`, `QRT 73`, `qrt thanks!`, etc.), the activator is dropped
  from the active list.
- **Park-change re-alert** — if a callsign you've already seen today shows
  up at a different park reference, the `NEW` tag is re-applied and a
  notification fires again.
- **Mode filter** — optionally restrict to a single mode (CW, SSB, FT8, …).
- **Watchlist** — flag favourite callsigns with a ★. Smart matching: a base
  call like `F5MQU` also matches `F5MQU/P`, `F5MQU/M`, etc.; a specific form
  like `F5MQU/P` matches only that variant.
- Each callsign links to its QRZ page.

## Activator tab

- **State picker** — choose any US state, DC, or territory. Loads every
  POTA-eligible park in that location.
- **Search** — free-text filter across reference, name, and grid.
- **Sortable columns** — click any column header (Reference, Name, Grid,
  Activations, Distance) to sort; click again to flip direction. Sensible
  per-column defaults (asc for text, desc for activations).
- **QTH radius filter** (optional) — enter your callsign and a radius in
  miles. The server looks up the callsign on [callook.info](https://callook.info)
  to get your QTH, then filters parks to those within the radius using a
  great-circle (haversine) distance. A **Distance** column appears
  automatically when the filter is active.
- Each park reference links to its page on pota.app.
- Parks responses are cached server-side for 5 minutes and callsign
  lookups for 1 hour, so flipping between states is snappy.

> The QTH lookup uses callook.info, which is US-only. International
> callsigns will return "Not found." Swap in HamQTH or QRZ if you need
> wider coverage.

## Requirements

- Python 3.10+ (standard library only; no `pip install` needed).
- A modern browser (Chrome, Firefox, Safari, Edge).
- macOS users with the Python.org installer: if you hit
  `SSL: CERTIFICATE_VERIFY_FAILED`, run the installer's cert script once:
  ```
  /Applications/Python\ 3*/Install\ Certificates.command
  ```

## Usage

```
python3 pota_web.py
```

Starts a tiny HTTP server on `http://127.0.0.1:5656/` and opens it in your
default browser. Leave the tab open. On first load, click *Enable
notifications* so alerts fire when the tab is in the background.

Stop with Ctrl-C. The port is a constant near the top of `pota_web.py` if
you need to change it.

## How it's wired

The server is just there to dodge CORS and shuffle a couple of files. Its
routes:

- `GET /` — serves the React page.
- `GET /api/spots` — proxies `api.pota.app/spot/activator`.
- `GET /api/parks?location=US-MA` — proxies POTA's parks-by-location
  endpoint.
- `GET /api/callsign?call=W1AW` — proxies `callook.info` for QTH lookup.
- `GET` / `PUT /api/watchlist` — reads / writes `watchlist.txt`.

All the real logic (polling, dedup, park-change detection, QRT removal,
band grouping, radius math) runs in the browser. React is loaded from a
CDN and the JSX is transformed in-browser by Babel Standalone, so there's
no build step. Per-day "seen" state, watchlist cache, selected state,
saved QTH, and selected tab are all persisted in `localStorage`.

## Watchlist

The repo ships with `watchlist.example.txt`. On first run, the server
copies it to `watchlist.txt` (which is git-ignored, so your personal list
stays local). One callsign per line; `#` starts a comment. Matching is
case-insensitive.

```
# Example
WB0RLJ
KJ7XJ
K4SWL
F5MQU/P      # only this specific variant
```

The web UI has a built-in editor under the **Watchlist** button that
writes straight to `watchlist.txt` — so you can edit it from the UI or
from your text editor, whichever you prefer.


## Notes

- The POTA API is public and doesn't require authentication, but please be
  kind to the servers — the 60-second poll interval is already plenty.
- On a cold start, the current feed is seeded silently so you don't get a
  burst of dozens of notifications at launch.

