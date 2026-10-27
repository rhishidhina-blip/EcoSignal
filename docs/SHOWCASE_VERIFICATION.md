# Verification and scope

The user supplied the v39 export dated October 26, 2026. Its ZIP integrity and original application/data hashes were checked. `V39_SOURCE_VERIFICATION.json` records its archive SHA-256 and source commit. Export-authored README/environment/ignore changes are kept distinct from application code.

The showcase adds documentation, recovered photo backend source, model metadata/evidence and source-only notebooks. It replaces the generated source-download page with a GitHub link and excludes recursive archive parts plus a partial temporary part. It does not change model inference, scoring, review or application business logic.

The export setup document records 167 tests and a production build passing on the published revision; these are supplied prior results, not a new complete build here. Earlier local component checks remain in `research/docs/CURRENT_COMPONENT_CHECKS.json` with their original scope, including two Windows cleanup errors for an earlier recovered multimodal backend. They must not be presented as v39 end-to-end test results.

No retraining, provider API calls, hosting migration or deployment occurred. Live D1/R2 data, private runtime secrets and personal observation exports are excluded. The website needs its existing storage/authentication bindings and external inference services for full behavior. A source repository alone does not provision those services.

Scientific results are run-specific. Historical coverage metrics at 0.55 do not identify current 0.65 performance. Baseline growth-form results do not identify filtered-model accuracy. GeoRisk V1 random-forest results differ from current V2 XGBoost. The unified indicator and quality/confidence diagnostics remain provisional; independent field validation is not established.
