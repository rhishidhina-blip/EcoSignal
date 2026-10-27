# Training records extracted from supplied files — October 26, 2026

These records were extracted from notebook source and saved outputs without executing training cells. Cell references in JSON are zero-based. They document saved runs; they do not automatically validate deployed weights.

| Run | Recovered training and evaluation record | Link to active model |
|---|---|---|
| Coverage v2 supplied notebook | 99 pairs; 64 train / 14 validation / 21 test; seed 42; 320×320 MobileNetV2 U-Net. Selected threshold 0.55. Saved test mean IoU 0.742648, Dice 0.821354, coverage MAE 4.588542 percentage points. | Notebook SHA-256 output exactly matches locally saved lichen_coverage_model_v2.keras (b7c52a57…). Active best_model (2).keras has different SHA-256 (0496f79a…) and threshold 0.65. No claim that the 0.55 metrics describe active inference. |
| Supplied growth-form baseline | 900 images; 720 train / 180 validation; seed 42; 224×224 EfficientNetB0. Class order crustose, foliose, fruticose. Saved validation report rounds accuracy to 0.78; saved review counts 140 correct / 40 incorrect. | Saves growthform_effnet_baseline.keras, not the active filtered_highacc checkpoint. No saved weight hash or independent test set. |
| Supplied GeoRisk historical V1 | 13-feature, 500-tree random forest; 300,000 training pixels from 2013–2015; 1,347,419 temporal test pixels from 2015–2022. ROC-AUC 0.7624; PR-AUC 0.2069; F1 0.2486; threshold 0.503483. Saved reload verification passed. | Current recovered GeoRisk V2 is a different XGBoost model with 21 features and later periods. Existing V2 metadata remains authoritative for V2. |

## Supplied image/mask archives

The owner describes their source as **online images**. Archive hashes and per-file image/mask hashes, geometry and native coverage are recorded in dataset-provenance.json and supplied-pairs.csv. The directory name CV_Chlorosis alone does not establish a chlorosis labeling task; the supplied notebook treats nonzero mask pixels as lichen foreground. Per-image URLs, creators, licenses and mask-annotation provenance remain unspecified. No permission to redistribute internet images is inferred. Original ZIPs remain at their supplied local paths; they were not added to a public repository or changed.

## Remaining exact-run links

1. Active coverage checkpoint 0496f79a…: matching run-bound metadata/evaluation and rationale for the active 0.65 threshold. The supplied notebook identifies historical b7c52a57… at 0.55.
2. Active growth-form filtered checkpoint e8a1bc90…: executed filtered-run split/file list and checkpoint-bound results. The baseline is now documented. The previously recovered filtered notebook has source/output inconsistencies and is not sufficient to establish those results.
3. Image attribution and annotation provenance: actual URLs/license records and labeling decisions. “Online images” is recorded accurately but is not per-image attribution.

The owner subsequently supplied the v39 website export, now included at the repository root. GitHub component repositories remain linked; none were downloaded during this training extraction.
