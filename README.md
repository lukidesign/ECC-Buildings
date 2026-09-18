# ECC Buildings

An interactive ECC spatial explorer for a connected city, apartment building, electrical room, and a conceptual low-voltage switchgear assembly. The interface supports Chinese and English.

![ECC Buildings city scene](web/public/assets/city.webp)

## Run locally

Requirements: Node.js 22.13 or newer and npm.

```sh
cd web
npm ci
npm run dev -- --host 127.0.0.1 --port 3000
```

Open [http://localhost:3000/buildings](http://localhost:3000/buildings). To run the checks:

```sh
cd web
node --experimental-strip-types --test tests/*.test.mjs
npx tsc --noEmit
npm run build
```

## Explore

- Follow the city → apartment → electrical room → switchgear route through scene hotspots or the navigation card.
- Drag the room panorama, use arrow keys to look around, and press Home to reset the view.
- Open the cabinet details for a conceptual overview and an application guide.
- Switch between Chinese and English without losing the current scene or room view. The preference is saved in the browser.
- On narrow screens, use the complete room still image and the vertical navigation.

The ECC theme uses `#2563EB` for its main interactive color, `#1D4ED8` for active text, and `#EFF6FF` for selected backgrounds. The palette is defined in `web/app/globals.css`.

## Project structure

| Path | Purpose |
| --- | --- |
| `web/components/landscape/` | Routes, language, hotspots, room panorama, and product sheet |
| `web/app/` | Layout, responsive scene styling, and theme |
| `web/public/assets/` | Optimized images, 8K panorama, transition video, and marker metadata |
| `source/build_scenes.py` | Editable procedural Blender scene source |
| `source/*.blend` | Editable scene masters |
| `source/render_delivery.py` | Exterior stills and city-to-apartment camera move |
| `source/export_assets.mjs` | Optimized web media export |

The runtime uses local assets and has no live equipment connection or backend data feed. The cabinet visuals and application text are conceptual, not a specified product or engineering drawing.

## Rebuilding media

The optimized media required to run the site is already under `web/public/assets/`. Blender 5.2 can rebuild the editable assets from `source/build_scenes.py`; the complete room panorama takes substantially longer than the still images. Source masters are included so the scenes can be edited without acquiring the reference site's models or media.

The scene assets were independently modeled as a visual study. Earlier site references informed the experience, but no reference-site video, model, or panorama is included in the app. No brand or equipment certification is implied.
