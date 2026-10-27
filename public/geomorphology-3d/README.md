# EcoSignal terrain observatory

A portable, same-origin 3D viewer for the existing EcoSignal website. It contains
real terrain and the actual saved GeoRisk display output. No Render changes,
API keys, browser Python runtime, model retraining or external CDN are required.

## Integration

1. Extract `EcoSignal_3D_Terrain_Integration.zip`.
2. Copy its `geomorphology-3d` folder into the existing Site framework's static
   asset folder. For a framework with `public/`, use `public/geomorphology-3d/`.
   Keep vendor and assets subfolders intact. Preserve the Site's current audience.
3. For React, copy `integration/EcoSignalTerrain.tsx` into your component folder,
   import it, and render `<EcoSignalTerrain />` in a new BioTerrain 3D view.
   The custom element uses Shadow DOM to keep styling separate from the Site.
4. For plain HTML, add:

```html
<ecosignal-terrain-viewer
  data-url="/geomorphology-3d/assets/terrain.json"
  metadata-url="/geomorphology-3d/assets/ecosignal_georisk_v2_1m_metadata.json"
  model-url="/geomorphology-3d/assets/ecosignal_georisk_v2_1m.joblib">
</ecosignal-terrain-viewer>
<script type="module" src="/geomorphology-3d/viewer.js"></script>
```

5. Alternatively, embed the complete standalone page:

```html
<iframe src="/geomorphology-3d/index.html"
  title="EcoSignal terrain observatory"
  style="width:100%;height:1050px;border:0" allowfullscreen></iframe>
```

Use the React/custom-element approach for automatic document height and no nested
iframe. Public paths must actually serve these files, rather than a framework's
fallback HTML page. The viewer requires WebGL 2. Open over HTTP(S), not file://.

For local preview, serve this folder with an ordinary static HTTP server.
The standalone page is the same production viewer, not a mockup.

## Behavior and scientific interpretation

- Terrain shape comes from aligned actual 2015, 2022 and 2024 DEMs, averaged
  to a 129 × 129 display grid (~254 × 238 m). Source DEM resolution is 1 m.
- Only cells with at least 99.5% measured coverage in every survey are shown.
  This fixed footprint avoids apparent changes caused by changing coverage.
- The default susceptibility surface uses the original 1300 × 1225 GeoRisk PNG,
  directly copied from the verified final model export. Native EPSG:32119
  vertex centers are transformed to EPSG:3857 texture coordinates before draping.
  The texture is about 31 m per pixel. The full-resolution scientific raster
  is a separate artifact and is not required for this viewer.
- Colors are actual 2024 model scores, not invented scores, future probabilities
  or elevations. Risk colors remain fixed at 2024 for historical/future surfaces.
- Point-inspection scores are approximate bins recovered from the original
  256-color inferno PNG. They are explicitly display values, not exact 1 m queries.
- 2025–2040 shapes are a **separate exploratory linear extrapolation**, not an
  output of the GeoRisk classifier. Per-cell OLS trends over the three observed
  dates are anchored to 2024. No future climate/development/event drivers are used.
- The trend hindcast's 2024 mean absolute error was 0.1943 m versus 0.1601 m
  for no change; RMSE was 1.3137 m versus 1.0641 m. The projection did not beat
  that baseline. These errors are coarse-cell averages, not guaranteed bounds.
- GeoRisk holdout ROC-AUC 0.8033, average precision 0.2694, precision ~10%,
  recall ~63%. Its ranking evaluation does not validate the future projection.
- Vertical-reference/geoid compatibility remains provisional. Elevation changes
  may include survey offsets, construction and other non-erosion processes.
- Vertical exaggeration defaults to ×40 for legibility and can be changed to ×1.

## Verification and deployment

See `data-verification.json`, `browser-verification.json`, and the bundle manifest.
Actual website integration/deployment is not performed by this package.
After installation, verify the 2024 texture and fixed footprint, 2040 scenario
label, layer switching, keyboard/touch interaction, model download and mobile
layout. Check existing satellite/AQI/chatbot views before publishing.

The application fetches only its same-origin static data/assets and performs no
tracking or external API calls. It never executes or unpickles model bytes.
Preserve the existing Site audience when serving the model download.

## Library

Three.js 0.186.0 and OrbitControls are vendored; MIT license included in vendor/.
The original source PNG was produced with Matplotlib's inferno palette. Palette
samples used for the legend and approximate score bins were read from the
upstream Matplotlib 3.10.3 colormap definition and matched to the saved PNG.

Official references: https://threejs.org/docs/pages/OrbitControls.html and
https://threejs.org/manual/pages/color-management.html.
