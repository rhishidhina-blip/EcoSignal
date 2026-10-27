# Production-native validation and field-data handoff

The validator loads and compiles the exact current `app/lib/unified.ts` and `app/lib/georisk-numeric.ts`, and uses the shipped numerical grid and fixed sampled-cohort CDF. It does not reproduce approximate notebook formulas. Output records the engine version, source SHA-256, as-of timestamp and reference version/hash. No API key, network request, model retraining or DEM re-inference is required.

## Real observation workflow

1. LichenLens: upload the actual photo; supply or import its real coverage output. Imported analysis may contain `site_id`, numeric `latitude`/`longitude`, `captured_at` with timezone, `model_version`, `coverage_percent`, `coverage_confidence` and optional growth-form class/confidence. Metadata prefills are unconfirmed. Synthetic-labelled imports stay illustrative.
2. Confirm that the photo, result, monitoring-site ID, coordinates, actual capture time and model run all describe the same observation. Do not use analysis/export time as capture time. Root confirmation and lichen confirmation are required; old or guessed joins are not approved.
3. Attach satellite + AirNow + terrain. Terrain also loads automatically after context confirmation. Inspect raw attributed AQI/category/timestamp/monitor distance, actual satellite dates/clear counts and nearby 20 m terrain sample/reference. Coverage and form remain raw outputs; form has zero weight. Unknown quality is not imputed.
4. Save on this device. Observations → Evidence & exports → **Export notebook site inputs** downloads `site_inputs.csv` and `EcoSignal-site-inputs.json`. JSON is preferred: it preserves exact nested input/provenance objects. The original full dataset snapshot remains available separately. Duplicate confirmed site IDs are excluded from this unique-site export until the user selects a visit; there is no automatic repeat-site join. Unconfirmed/example records are excluded with reasons. Missing/stale domain fields remain missing/stale, not silently filled.
5. Download the full source checkpoint, install its package dependencies, then run from its EcoSignal directory:

```sh
node scripts/validate-site-export.mjs /path/EcoSignal-site-inputs.json --out outputs/production-validation
# Equivalent flat CSV input with the complete supplied schema:
node scripts/validate-site-export.mjs /path/site_inputs.csv --out outputs/production-validation
# Reproduce a historical engineering-eligibility check explicitly:
node scripts/validate-site-export.mjs /path/EcoSignal-site-inputs.json --as-of 2026-10-14T00:00:00Z --out outputs/reproduced
```

Default as-of is current time, not the export timestamp. Outputs are local `validation.json`; no observed input or result is sent to the Site. An exported raw input is not automatically eligible. The runner applies production freshness/location/source gates and resamples numerical GeoRisk from the verified shipped lattice, matching automatic terrain attachment in the Site. It does not invent missing satellite or AQI inputs. No placeholder quality values are introduced.

## CSV schema and required metadata

The header-only schema is available at `/unified/validation/site_inputs_TEMPLATE.csv`; it contains no sample sites. Minimum actual biological observation: nonblank stable `site_id`, `observation_id`, latitude/longitude, `captured_at` with timezone, `site_id_confirmed=true`; coverage %, model/source version, lichen source/location/date and `lichen_confirmed=true`. Model confidence can remain blank; growth form is optional and unweighted.

AQI needs raw AQI 0–500, official category, AirNow source/version/URL, dated reading, actual requested coordinates and monitor coordinates. Default engineering gates: <=6 h old, monitor <=50 km from the confirmed site, photo/AQI alignment <=6 h. Unknown AQI quality remains blank. These thresholds are not scientific guarantees.

Satellite needs NDVI/NDMI/BSI/MNDWI, clear counts, valid pixel count, source/version, actual source timestamp, query coordinates, patch=3 pixels at native20 m and `sentinel-anchors-provisional-v1`. The observed pixel sample is approximately60 m wide, not a1 km aggregate. Satellite and photo must be <=30 days old; biological output must align with capture within1 h. Fixed historical terrain reference is2024 with year precision; nearest20 m lattice point uses the complete1,473,136-sample CDF version `georisk-2024-native-features-20m-sampling-v1`. Its original1 m features do not make an exact arbitrary-location1 m prediction. Model/DEM/feature and binary hashes, row/column, sample spacing and distance are preserved.

A flat legacy CSV with only lat/lon/coverage cannot become eligible: absent IDs, confirmations, capture/model/source metadata, monitor geometry and dated measurements are reported. JSON export retains unknown quality and complete provenance; the CSV intentionally leaves uncalibrated quality/confidence unknown. The runner ignores chlorosis, image/mask paths alone and unreviewed training labels as unified-domain inputs.

## Observed analyses and scientific limits

Only complete, confirmed, non-example unique sites at at least five distinct recorded locations enable descriptive observed robustness. Ablation removes one weighted domain at a time and explicitly normalizes analysis weights; zero-weight form is never counted or ablated. Sensitivity uses1000 seeded ±25% perturbations. Mean/max score change, Spearman rank correlation and top-decile overlap describe robustness, not accuracy or optimal weights. Unique IDs/locations do not establish statistical independence; spatial autocorrelation and sampling bias still need review.

Independent validation remains `not_run` without appropriately defined independently measured target constructs and aligned source/date/geography. Unrelated target definitions must never share one MAE. Spatial-block descriptive evaluation is not trained held-out predictor validation. Fixed35/15/25/25 weights and coverage inversion remain provisional; low visible coverage is not pollution evidence.

## Evidence recovered in this audit

Available workspace data has only satellite summaries/rasters and numerical terrain tests; no real located dated lichen records, repeat manifest, site-input table or independent ground truth was found. The user checked the current Chrome profile: zero saved observations. User-local four-row coverage files have42/68/28/74 plus form/confidence, but no IDs, dates, source provenance or confirmation: **unverified examples**, excluded. Chlorosis-only outputs and trainable-label image/mask paths have no matched site/date. Earlier TREE-001 coverage69.5573%, confidence.3728 is an incomplete historical notebook result, never assigned coordinates or seeded into records. There are zero available complete observed scores; ablation/sensitivity are not evaluable; independent validation is not run.

V22 live backup was fully verified:122715371 bytes,337 ZIP members, SHA-256423148b323bb524fb09d7f831969f2545de65b460236ed6c3aaca8480456d6a8. Every live part and ZIP CRC passed; no Git credentials, environment files, dependency directories or device observation database are present. `/index.html` canonically redirects307 to `/unified/source-backup/` (200). The final backup is regenerated to include this runner/schema and export implementation, so its new hash/size are in the final live manifest.

Browser evidence supplied by the user: illustrated scan flow remains0/4 domains,0% eligible and attachment disabled; source backup downloaded and verified; approximately370 CSS-px zoomed layout fits with no horizontal scrollbar. The subsequent October 23 cloud audit verified 320/360/390 px iframe viewports at Photograph/Context/Results with scrollWidth equal to clientWidth, plus the standalone desktop at 1348 px content width. Private production visual QA still requires cloud-session sign-in; these are preview checks. Software/build checks are separate from visual and scientific validation.

Current audit: all scoring dates require a valid ISO timestamp with timezone and real calendar date. Satellite and capture must be within 30 days of each other, in addition to both freshness gates. MNDWI is water context only, not a fourth weighted satellite index. Component contributions are displayed only for a complete score; their sum equals the composite. Growth form remains explicitly excluded from scoring under the later approved coverage-only biological method.
