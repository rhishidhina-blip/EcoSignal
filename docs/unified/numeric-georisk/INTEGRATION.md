# EcoSignal numeric GeoRisk integration

Real numeric scores from the frozen 21-feature, 250-tree GeoRisk V2 model and hash-verified 2024 DEM; original 1m feature code, square validity footprint and 2015/2022/2024 common coverage. No retraining, no PNG colour decoding.

Decode georisk-2024-samples.u16 as little-endian uint16, shape from manifest. 65535 is nodata; other values /10000 are uncalibrated raw susceptibility. Native feature sample centers are regularly spaced 20m in EPSG:32119. Convert WGS84 to the manifest CRS, round offsets from first_sample_center_xy to nearest row/column, reject out-of-grid or nodata. No interpolation/fill across missing cells. Show that the estimate is sampled at a nearby 20m lattice point, at most about14.15m from a queried coordinate inside a grid cell.

Use georisk-reference-cdf.json cdf_percent[quantized_value] for percentile. This fixed cohort contains all1,473,136 valid lattice samples across common coverage. It is a documented sampled-coverage percentile, not the original full1m-pixel CDF and not a calibrated erosion probability. Keep this version fixed across users and map panning.

georisk-sampling-fixtures.json has24 real numeric inference locations for sampling tests only. They are not lichen field observations and must not be saved as observed scans. numeric-verification.json records independent re-inference, coordinate and CDF checks.

Integrate server-side or via same-origin static assets, preserve Site audience, keep existing overlays/3D and35/15/25/25 unified weights. Preserve all source dates and exploratory limitations. Do not require GitHub or Render for this static numerical dataset.
