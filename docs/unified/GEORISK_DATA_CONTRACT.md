# Numeric GeoRisk handoff

The app will adapt the actual numerical files supplied, rather than requiring an invented observation or a reconstruction from the PNG. A numerical sampled grid regenerated from the exact saved model and verified 2024 DEM is acceptable when its provenance and sampling are documented. The engine supports `numeric_grid` and `numeric_raster` source samples. Neither denotes a display-palette lookup.

Please preserve in the export:

- Numeric raw susceptibility values, geographic CRS/transform or per-cell WGS84 coordinates, valid-coverage/no-data mask, grid resolution and sampling footprint/method. Distinguish native DEM resolution from the exported grid spacing; neither implies a 1 km aggregate.
- The actual model and DEM identifiers/hashes, 2024 reference date/year, feature names/order, any downsampling or missing-feature handling, generated-at timestamp and numerical output hash. Regeneration date does not become the terrain observation date.
- A fixed, versioned reference cohort: at least 100 finite raw values (or an explicitly documented equivalent CDF adapted at integration), its AOI/mask, source product hash, sample size, sampling method/seed and limits. Freeze the cohort independently of visitors' chosen locations. Site-specific outputs must use that same numerical source/model and reference.

Current pure-engine sample fields include location, source, version, observed_at, raw, year=2024, kind, footprint_m, reference_id and raster_sha256. The legacy `raster_sha256` field also identifies the numerical grid product hash; it must match the reference's numerical source hash, not the PNG or model file hash. Model and DEM hashes remain additional provenance, not substitutes for the numerical product identity. The reference includes id/version/source, source hash, year, WGS84 bounds, sorted finite values and sampling description.

Values become relative fixed-CDF ranks, never probabilities, predicted lowering depths, elevations or future risk. Unknown per-sample quality/confidence stays unknown; global holdout metrics do not become individual-sample confidence. No complete observed score, ablation/sensitivity or independent validation is claimed before eligible real site inputs exist. The current production app still has no numerical GeoRisk data to sample; integration follows receipt and verification of those bytes.
