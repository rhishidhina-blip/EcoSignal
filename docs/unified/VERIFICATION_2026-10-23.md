# EcoSignal unified screening — technical audit

Audit date: 2026-10-23. Engine: `EcoSignal-Unified-Provisional-v3.1.1`; input schema 1. Latest source was recovered from published v23 (`ebb38d7edafa941a2849dd6c0a44a5de54a1ee7b`) before editing. Site audience is preserved. This report describes software verification, not independent scientific validation.

## Checklist disposition

| Concern | Verified behavior / remaining evidence |
|---|---|
| Weights and growth form | 35% satellite, 15% AQI, 25% visible coverage, 25% terrain. Growth form is explicitly excluded (0%) and retained as optional context. The earlier 16.67%/8.33% split was superseded by the user's later approved coverage-only method, not silently redistributed in this audit. Unsupported ecological ordering is not used. |
| Direction and duplicate counting | All weighted components map to 0–100 higher relative concern. Four domains; zero-weight form never counts toward availability or ablation. Fixed weights are provisional, not statistically optimized. |
| Satellite normalization | 45% inverted NDVI anchors [.2,.8], 35% inverted NDMI [-.2,.5], 20% BSI [-.3,.3], each clipped 0–100. MNDWI is water context, with no extra weight or generic harm interpretation. Land-cover/season-matched calibration remains unavailable. |
| AQI normalization | 100 × clip(raw AQI/300,0,1). Official raw AQI/category/source/date remain separate. AQI >300 saturates the screening subscore; it does not change the official AQI. No invented quality .6. |
| Biological normalization | 100 − coverage %, a provisional visible-coverage heuristic. Low coverage is not pollution evidence, species tolerance, or a measurement of harm. Actual coverage/form/model confidence remain available. |
| Terrain normalization | Actual numerical frozen-model output, uint16 little-endian /10000; nodata65535. Fixed CDF over 1,473,136 valid 20m samples, version `georisk-2024-native-features-20m-sampling-v1`. No PNG colors, interpolation or future-risk inputs. Not the full original 1m-pixel CDF. |
| Incomplete inputs | A full score requires all four positive-weight domains. Missing/invalid/stale/unconfirmed/example inputs produce no composite, not zero risk. Partial totals are disabled; missing inputs and eligible nominal weights are visible. No silent renormalization. |
| Site integration | Scan results, imported analysis, confirmed saved observations and selected saved-site map panel use the same scorer. Numerical terrain automatically resamples after confirmed context. Changing context clears environmental joins; late requests cannot attach to a different site/capture. |
| Repeat observations | Observation IDs remain distinct. Same-site joins need explicit confirmation; blank IDs and ambiguous sequences are rejected. Unique-site validation exports exclude duplicate site IDs until a visit is selected. Repeats are not independent samples. |
| Arithmetic / versioning | Weighted contributions are returned by the pure production engine and displayed for complete scores. Sum, boundaries, monotonicity, determinism, missing inputs, weight scenarios and version metadata tested. |
| Real complete site | Not available: zero verified located/dated biological records. No real complete score, observed sensitivity/ablation or independent validity claim was fabricated. |

## Eligibility gates

- Nonblank confirmed site ID; valid coordinates; real capture date <=30days old; examples excluded.
- Dates must be valid calendar ISO timestamps with explicit timezone. Invalid dates, absent zones and future source timestamps are rejected.
- Satellite: native20m, 3×3 pixel neighborhood (approximately60m), actual finite indices and clear counts>=1, source/version/reference and query coordinates. Satellite source and capture are each <=30days old and separated by <=30days. This is not a1km aggregate.
- AirNow: actual attributed reading <=6hours old; monitor coordinates and distance<=50km; capture/reading separation<=6hours. These are engineering gates, not scientific guarantees. Current AirNow is not retrospectively assigned to old photos.
- Biological output must be explicitly confirmed with source/model version and location; output date within1hour of capture. Confidence may be unknown and is not invented.
- Source/query coordinates within100m of confirmed site. Numerical terrain request within1m; nearest20m lattice sample distance<=14.142137m, valid in-coverage/nodata checks, fixed reference/hash/year2024. Model, feature-code and DEM hashes retained. Terrain2024 is historical context with year precision, not a contemporaneous measurement. 2040 projections are excluded.

## Tests completed

`node --test tests/*.test.mjs`: **96 passed, 0 failed**, after a production build. Includes all24 numerical terrain fixtures; full binary hash/endianness/dimensions; all10001 CDF entries against the full sampled-cohort histogram; nodata/bounds/nearest rounding; a synthetic complete four-domain flow; each missing/invalid/stale/future/source/location gate; exact AirNow age/distance boundaries; unknown quality; repeat-site handling; versioning; zero-weight ablation; import/export schema and CSV; empty/unverified/example validation inputs; and existing chat/AirNow/satellite/2D/3D software regressions.

`node node_modules/typescript/bin/tsc --noEmit`: passed.

`node scripts/validate-site-export.mjs public/unified/validation/site_inputs_TEMPLATE.csv --out outputs/current-audit`: input_count0; eligible_complete_unique_sites0; ablation/sensitivity not_evaluable; independent_validation not_run. The runner compiles the actual production scorer/sampler; no notebook approximation.

`PYTHONPATH=<audit-dependencies> python scripts/verify-native-satellite.py <satellite_results_preview_fixed.zip>`: passed. All4 original latest-week GeoTIFF hashes, affine transforms, CRS and bands verified. **All169 lossless Float32 chunks and their nodata values equal the uploaded original TIFFs**, across8 bands. No display colors used for scoring. Optional audit dependencies: numpy/rasterio.

Synthetic robustness tests exercise four domain ablations and1000 seeded ±25% perturbations. These are software fixtures only; no observed robustness or predictive accuracy is claimed.

## Cloud-browser QA

Used the remote cloud browser, not the user's computer. Managed preview:

- At320/360/390px iframe viewports: Photograph, Context and Results each have document scrollWidth equal to clientWidth (305/345/375 respectively, accounting for15px vertical scrollbar). No horizontal overflow.
- Standalone desktop content width1348px: Photograph/Context/Results each have scrollWidth1348.
- Example result:0/4 eligible domains,0% nominal coverage, no composite; attachment disabled. Growth form visible at0weight; exclusion and coverage-only method explicit.
- Temporary isolated browser harness executed the actual production scoring module: satellite50 × .35=17.5; AQI50 × .15=7.5; coverage50 × .25=12.5; numerical terrain percentile71.01055164 × .25=17.75263791; total **55.25263791**. Removing AQI produced3/4 domains and no score. Harness and responsive wrapper were removed before publication; no synthetic device observations saved.
- GeoRisk2D layer switching removed/restored overlay, slider reached0, fit-to-coverage control operated. Satellite/AirNow panels and3D wrapper/model download remain present.

Limits: private production UI needs sign-in in this new cloud session. The HTTP preview cannot complete secure Web Crypto integrity checks; the production HTTPS assets are verified independently. This cloud browser reported **WebGL context creation unavailable**, so 3D rendering/timeline interaction could not be visually verified here. Existing source tests cover timeline through2040, surface switching and fixed2024 colors; this does not replace WebGL visual QA. Exact mobile checks above use preview iframes, not physical devices.

## Production and backup checks

Pre-update live v23: home/schema/README/3D viewer/numerical manifest/CDF/binary all HTTP200. Binary5031936bytes matches SHA256 `cb1bd7e15d47cbbd9d2a4282108061ca17b5d1600c9e13b78c29934f47309ec7`. AirNow HTTP200 with source/category/timestamp/monitor coordinates. One chatbot request timed out504; graceful timeout/retry handling remains in the existing frontend; a final post-publication probe is reported separately.

`/unified/source-backup/index.html` redirects to canonical `/unified/source-backup/`, HTTP200. All8 previous backup parts and assembled ZIP hashes/CRC verified; previous v23 backup122735832bytes,344members, SHA256 `92b73e67381fbe15df5879da53154bea69106b3039637897f5f6ef06e13533cc`. The final backup is regenerated with this audit, timestamp changes, tests and source-audit script; consult the final manifest for its new checksum. No credentials, environment secrets, Git metadata, dependencies, build output or device observations are included.

Production paths: `/api/air-quality?lat=35.8&lon=-78.7` (GET), `/api/ask` (POST question JSON), `/unified/georisk/georisk-numeric-manifest.json`, `/unified/georisk/georisk-2024-samples.u16`, `/unified/georisk/georisk-reference-cdf.json`. Scoring and terrain sampling are client functions, not separate HTTP APIs: `app/lib/unified.ts::score`, `app/lib/georisk-numeric.ts::lookupGeoRisk`.

## What actual field data must still supply

A genuine photo-linked coverage output plus confirmed site/observation IDs, coordinates, actual timezone-qualified capture time and model/source version. Optional growth-form output stays context. Attach eligible AirNow and satellite data and a valid numerical terrain point. Real-photo analysis is imported from the user's model; this frontend does not fabricate an image prediction.

User-local four-row coverage files42/68/28/74 lack IDs/capture dates/provenance/confirmation: unverified examples. Chlorosis/image-path-only outputs lack matched sites/dates. Historical TREE-00169.5573% confidence.3728 lacks matched inputs and is never seeded into observations. Current browser profile was reported empty. There are **zero available complete observed sites**.

Observed ablation, ±25% weight sensitivity, component dependence and independent field validation remain not evaluable/not run. At least5 eligible unique complete sites at distinct locations enable descriptive robustness in the runner, not proof of independence. Suitable independent target constructs, aligned outcomes, land-cover/season references and a defensible scientific weight justification remain research work. Different outcome constructs must not be pooled into one MAE. The indicator is usable as a transparently provisional screening tool; software tests do not make it a validated environmental-health measure.

Export flow/schema: see `/unified/validation/README.md`, `/unified/validation/site_inputs_TEMPLATE.csv`. Observations → Evidence & exports → Export notebook site inputs provides the production-native JSON/CSV. Source backup includes the runner, schema, tests, data references and methodology.
