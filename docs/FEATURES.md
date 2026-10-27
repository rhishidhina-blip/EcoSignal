# Feature implementation guide

The root [README](../README.md#features-and-supporting-code) contains the complete feature catalogue, including core application features, all 19 research-workspace workflows, environmental scoring and Ask LichenLens. Every feature is linked to its implementing source.

For deeper implementation detail:

| Area | Detailed source documentation |
|---|---|
| Nineteen evidence, review, data, quality, mission and repeat workflows | [Integration](features/INTEGRATION.md), [recorded validation](features/VALIDATION.md) |
| Photo inference and website adapter | [Integration](PHOTO_ANALYSIS_INTEGRATION.md), [Keras replacement](../services/photo-analysis/MODEL_UPDATE.md) |
| Unified scoring and component weights | [Implementation](unified/IMPLEMENTATION.md), [production validation](unified/PRODUCTION_VALIDATION.md) |
| Numerical GeoRisk geography and fixed reference | [Data contract](unified/GEORISK_DATA_CONTRACT.md), [numerical integration](unified/numeric-georisk/INTEGRATION.md) |
| Observation and image chat | [Context contract](chat/MULTIMODAL_INTEGRATION.md), [saved validation](chat/VALIDATION.json) |
| Actual training runs and deployed-model distinctions | [Training records](TRAINING_RECORDS.md), [notebook provenance](NOTEBOOK_PROVENANCE.json) |
| Source snapshot and packaging changes | [v39 identity](V39_SOURCE_VERIFICATION.json), [showcase scope](SHOWCASE_VERIFICATION.md) |

Historical documentation includes earlier version descriptions and deployment states. The root README describes this v39 source tree; historical notes do not prove the current state of external live services.
