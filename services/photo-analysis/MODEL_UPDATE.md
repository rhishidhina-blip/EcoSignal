# Coverage-model replacement — October 24, 2026

This update replaces the selected PyTorch coverage model with the exact supplied `best_model (2).keras`, installed as `models/lichen_coverage_v2.keras`. SHA-256: `0496f79a349de607d43f6e3db3f05fe542e7d76ee13e46bf7b352feae7db3133`.

The user explicitly selected threshold **0.65**. Input is RGB float [0,1] resized bilinearly to 320 × 320; the model includes its own Rescaling(2,-1). It is loaded with compile=False, so custom training losses are not required. No PyTorch dependency remains in active inference. The growth-form adapter and model are unchanged.

Coverage is measured on the thresholded native 320 × 320 mask. Display masks are enlarged with nearest-neighbor resizing to preserve their labels. The old PyTorch adapter's morphological cleanup is not applied to this newly trained model. Existing heuristic review diagnostics are retained but explicitly identified as uncalibrated for this replacement.

## Apply in the existing Codespace

Upload `Coverage-Model-Update-065.zip` into the Codespace's repository root. Stop the running API with Ctrl+C before replacing files, then run:

```bash
unzip -o Coverage-Model-Update-065.zip
.venv/bin/python coverage-update/apply_update.py .
```

The installer checks every supplied file and refuses to overwrite existing backend files with unrecognized changes. Old files are copied to `.coverage-model-backup-20261024/`. The old `.pt` model is retained for rollback but is no longer loaded.

Commit only the replacement files, without adding uploaded photos or the update ZIP:

```bash
git add api/coverage.py api/coverage_quality.py api/main.py models/lichen_coverage_v2.keras models/coverage_metadata.json tests/test_coverage_v2.py requirements.txt Dockerfile
git commit -m "Replace coverage model with Keras v2 at threshold 0.65"
git push
```

Restart using the existing token environment:

```bash
.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

If a new terminal reports that `ECOSIGNAL_API_TOKEN` is missing, set the token in that terminal before restarting. Do not put tokens in GitHub. Reuse the existing token if a frontend already depends on it; generating a new token requires updating that frontend's server secret too.

The `/health` response must show `coverage_mobilenetv2_unet_320_v2_t065`. Restarting is necessary because the old process keeps its loaded model in memory.

## Verification

- 9 tests passed: original API contracts plus model checksum selection, threshold boundary, RGB preprocessing, invalid-output rejection, native-mask coverage, and preservation/alignment of small mask regions.
- The real replacement and unchanged growth-form model loaded successfully using the existing Python 3.12 / TensorFlow 2.21 environment.
- Both original Apex Nature Park JPEGs returned HTTP 200 and generated aligned 1200 × 1600 masks/overlays.
- Photo 0790: 2.265625% model-predicted coverage, review warnings.
- Photo 0792: 0% model-predicted coverage, rejected by the inherited heuristic quality gate; retain for review, not as a confirmed zero-lichen measurement.
- No ground-truth validation or retraining was performed. These results establish executable integration, not scientific accuracy.
- No remote deployment or server restart is implied by downloading this package.
