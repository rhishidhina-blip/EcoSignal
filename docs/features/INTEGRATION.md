# EcoSignal evidence and adaptive-planner integration

This update ports the supplied notebook workflows into the existing Sites/Cloudflare runtime. Python/FastAPI/SQLite cannot execute inside this Worker; equivalent workflow rules now use D1 and R2, while actual OpenCV runs in the visitor's browser. Notebook definitions and source hashes are retained under notebook-reference; executed notebook outputs and photographs are not published as assets or sample data.

## What runs where

| Capability | Host | Configuration |
| --- | --- | --- |
| Observations, predictions, review, staging, frozen datasets, models, learning queues, audit, missions | Existing Site: native D1 | DB binding; schema-only migrations applied by Sites |
| Scientific image assets | Existing Site: native R2 | BUCKET binding; authenticated asset routes |
| Image quality, mask framing, ORB/RANSAC repeat alignment | Browser; same-origin vendored OpenCV 4.12.0 | No API key or external service |
| Numerical terrain lookup and imported-pool planner ranking | Existing Site and browser | Import the real Render backend ZIP produced by planner notebook; no separate planner host required |
| Optional remote adaptive planner | Python Render service | ECOSIGNAL_PLANNER_URL + ECOSIGNAL_PLANNER_TOKEN in Sites; PLANNER_API_TOKEN on Render |
| Coverage and growth-form model inference | Existing external image-analysis backend | ECOSIGNAL_ANALYSIS_URL + secret ECOSIGNAL_ANALYSIS_TOKEN; unchanged |
| Ask LichenLens | Existing configured chatbot backend | Preserved |

The attached Sites adapter contains no real candidate pool or Render deployment address/token. Until a real pool is imported or a remote planner is configured, the planner reports missing inputs; the old five example recommendations and hard-coded 632 count are removed. Import Observations → Research workspace → Missions & planner → Render backend ZIP. Only data/candidates.json and data/manifest.json are extracted; backend code is never executed by the importer. Source-file integrity, actual numeric raw values/percentiles at all candidate coordinates, the fixed coverage/reference, access-screening flags and candidate IDs are checked before persistence. A local plan uses only confirmed dated source/version-attributed records, unique confirmed sites, <=30-day captures, <=1h coverage alignment and actual within-coverage coordinates. Missing or conflicting data is excluded, not made safe.

## Feature entry points

All tools are reachable in Observations → Research workspace; guided capture is also available beside the scan flow, and the planner is in Fieldwork.

| Feature | Implementation |
| --- | --- |
| 1 records / outputs | Authenticated durable observations and separate immutable predictions; device copies retained |
| 2 scientific assets | Immutable R2 objects, SHA-256, deduplication, sample/source lineage, authenticated retrieval |
| 3 inference boundary | Existing photo proxy plus stored per-model predictions with actual versions/statuses |
| 4 corrections | Structured coverage/form/corrected-mask proposals and withdrawal; original unchanged |
| 5 independent review / staging | No self-review or duplicate vote; mask requires two independent approvals; reviewed staging only |
| 6 dataset versions | Draft → immutable frozen manifest with checksum; confirmed site grouping; database-enforced cross-version split guard |
| 7 exports | Reviewed frozen JSON, CSV, GeoJSON and ZIP with images/masks and checksums; bounded portable exports |
| 8 provenance | Server-actor audit chain, per-run steps, file hashes, chain verification |
| 9 failures | Standard failure envelope/catalog and masked service errors; request IDs |
| 10 registry | Required model-card fields, lifecycle states, actual artifact hash, frozen-data requirement before production |
| 11 learning queues | Separate missing-output, model-reported uncertainty and geospatial-gap queues; stable IDs/statuses; no automatic retraining |
| 12 reviewer dashboard | Type/version/confidence/site/date/status filters and independent decisions; server authorizes actions |
| 13 reanalysis / comparison | New immutable runs/predictions; compare same observation/model type without overwriting originals |
| 14 quality gate | Actual blur/exposure/contrast/resolution checks; recorded metrics/thresholds; retake blocks pipeline |
| 15 pipeline | Quality gate → real model service → saved steps/predictions/available environmental source context → quality components; explicit partial/failure states |
| 16 confidence | Explicit known/missing components, nominal weights and available-weight index, separately labelled uncalibrated quality |
| 17 field missions | Real imported-pool priorities, deduplication of active missions, claim/checklist/confirmed-site completion, audit |
| 18 repeat monitoring | Explicit same-surface/order confirmation, ORB + RANSAC, valid-overlap comparability and matched-model-MAE interval; insufficient evidence yields unavailable |
| 19 guided capture | Actual image metrics and specific retake instructions; accepted-mask framing when available; annotated local overlay |

## Method changes and boundaries

- Unified environmental indicator remains satellite .35, AirNow .15, visible coverage .25, numerical terrain .25; form remains unweighted context. Existing source/date/geospatial gates and fixed CDF stay unchanged.
- Planner's current_georisk_review_v1 profile remains explicitly separate: .28/.75 terrain, .24/.75 review need, .18/.75 coverage gap, .05/.75 diversity. Historical-change/control terms are explicitly inactive in the local Sites port; no row-wise redistribution. Local method is versioned v3.0.0-sites1. Optional remote service can retain the notebook runtime.
- OpenCV's legacy self-resolving thenable is removed only after runtime initialization to avoid a loader loop. No external CDN.
- Repeat alignment retains ORB3500 / ratio .72 / RANSAC4px and notebook weights/thresholds. SSIM/exposure are calculated only over valid aligned overlap, avoiding warped black-border contamination. This is an explicitly versioned Sites adaptation, not numerical parity with the old rectangle implementation.
- MAE 3.9827 from the historical notebook is NOT applied by default: the exact coverage artifact has not been verified against that evaluation. The user must supply/confirm matched-model MAE, and the actual coverage versions must match. Two images never establish a trend. Unknown actual dates remain unavailable; no upload/export time substitutes for capture time.
- Quality and framing are provisional heuristics, not calibrated confidence. Missing framing is shown as base-quality-only, with 85% nominal quality weight known. Confidence aggregation preserves notebook weights but explicitly exposes unknown components and known-weight normalization; it is not the unified score, probability of correctness, or environmental health.
- Production registry claims require a frozen reviewed training version, validation status and artifact hash. Registry registration does not change the external inference service's loaded weights. Unsupported model version selection fails explicitly.
- Independent reviewers must be real different signed-in visitors already authorized by the Site audience. This update does not add viewers or change audience. An owner alone cannot perform independent approvals.
- Workspace records are shared with the current Site audience; server identities scope all evidence to this private project workspace. Client requests cannot invent reviewer identities. No notebook fixtures or demo observations seed the production database.
- No full observed unified score, observed ablation/sensitivity, external accuracy or scientific validation is claimed. Independent scientific validation remains not run.

## Operations / limits

Data are in D1/R2, not the Worker's ephemeral filesystem. Assets <=8MiB, full upload stream <=9MiB, image headers <=60M pixels; photographs must decode through OpenCV before reanalysis. Readable quality is computed in the browser and attributed as such. Main photo workflow performs the base quality gate before model inference. Model-mask QA is kept separate.

Metadata reads are bounded to the latest 1,000 records per entity kind in this first implementation. Portable datasets are bounded to 100 reviewed observations and ZIP image contents <=32MiB; use multiple explicitly versioned collections when larger. Candidate import is bounded to 20,000 rows. Local requests reject unknown or illustrative sources, missing dates/confirmation, nodata and false reference matches. A candidate access label remains a screening label, not permission to visit.

The original standalone FastAPI database is not silently imported from Google Drive. Existing browser observations stay available; saving a new real scan also saves it to Sites, confirmed context changes sync automatically and refresh the planner, and the workspace has explicit migration/sync buttons for existing real device records. Reanalysis uses the real connected backend; unknown historical model performance is not attached to new photos.

User testing is intentionally left to the human. Software tests use an isolated local D1/R2 environment and synthetic fixtures; nothing is seeded into production. OpenCV primitives and actual textured/blank synthetic matrix alignment are tested without claiming browser visual QA or field accuracy. Full software results are in VALIDATION.md.
