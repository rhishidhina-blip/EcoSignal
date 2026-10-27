# Research and training notebooks

These notebooks preserve recovered code and markdown. Saved cell outputs and execution counters are cleared to keep Git reviewable and avoid embedding photographs, device paths in outputs, and multi-megabyte plots. Original notebook hashes and counts of cleared output bundles are in `../docs/NOTEBOOK_PROVENANCE.json`. Originals remain recoverable locally; clearing outputs does not indicate a newly executed run.

- `user-supplied/`: latest supplied coverage, baseline growth-form and historical GeoRisk V1 notebooks.
- `training/`: corrected coverage v3 (no recovered trained v3 weights) and filtered growth-form source (source/output run association unresolved).
- `georisk/`: current V2 reviewed/runtime workflow; V1 is separate.
- `satellite/`: weekly Sentinel-2 processing and preview repair.
- `validation/`: provisional unified-score analyses and missing-data handling.
- `planner/`: candidate preparation and uncertainty workflows.
- `field/`: original repeat-scan/guided-capture workflows.
- `assistant/`: grounded-chat and knowledge/context experiments.
- `historical/` and `research/`: earlier experiments, including synthetic-data framework and chlorosis research; not active product claims.

Read `../docs/TRAINING_RECORDS.md` before citing accuracy. The matched 0.55 coverage run is a different checkpoint from active 0.65 inference. Baseline classifier accuracy is not filtered-model accuracy. No notebook is automatically executed by repository import.
