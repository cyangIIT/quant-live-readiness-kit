# Launch assets

## `social-preview.png` (1280 × 640)

GitHub's recommended social-preview size. Used for OpenGraph / Twitter
card / LinkedIn previews when the repo URL is shared.

To upload (GitHub UI):

1. Go to the repo on GitHub → **Settings** → **General**.
2. Scroll to **Social preview**.
3. Click **Edit** → **Upload an image…** and select
   `assets/social-preview.png`.

GitHub does not provide a public REST API for setting the social
preview image — it must be uploaded via the web UI.

## `social-preview.svg`

Source vector for the preview. Edit this file if you want to rework
the layout; regenerate the PNG from it with any SVG-to-PNG tool
(`cairosvg`, Inkscape, a browser + screenshot).

The bundled PNG was generated with a Python + Pillow script that
replicates the SVG layout exactly; see the commit log for the
regeneration command.
