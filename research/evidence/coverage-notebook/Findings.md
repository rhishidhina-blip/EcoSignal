# Coverage notebook diagnosis and repair

The uploaded run does not establish field readiness. It achieved mean IoU **0.74265** and coverage MAE **4.58854 percentage points** on 21 test images at threshold **0.55**. These are different results from the earlier chat. Its saved phone-image example predicted **0.61%** coverage despite visible pale patches that merit annotation review.

| Area | Evidence and correction |
|---|---|
| Preprocessing | Training and field paths both use RGB `[0,1]`. MobileNetV2 retains the upstream `2*x-1` scaling in the original graph; the local graph test confirms this. A normalization bypass is not the demonstrated cause. The new graph makes scaling explicit and uses a single EXIF-aware loader and resize function throughout. |
| Label masks | Original `>0` decoding can promote compression noise, antialiasing and arbitrary colors to foreground. Saved masks look coarse in places; incomplete annotations remain a possibility. The revision enforces explicit lossless binary classes, preserves palette indices, checks geometry, and requires overlay review. Actual source masks were unavailable for verification. |
| Leakage | The original random image split has no duplicate, specimen or site safeguards. Leakage is possible, not proven. The revision groups exact/near duplicates and supplied source groups before splitting, rejects duplicate stems/unpaired files, and exports audit records. Hashes cannot replace known specimen/site IDs. |
| Generalization | Only **64 training images**. Validation: **one negative and no very-low-coverage images**. Test: one negative and one very-low-coverage image; the latter had **20.19-point coverage error**. Visible holdout examples often contain larger, distinct patches than the phone photograph. Domain shift and missing growth-form/texture/scale diversity are the leading explanation, requiring representative labeled data. Joint crops, scale variation and broader image-only augmentation are added as experiments, not evidence of improvement. |
| Interpolation | Original image bilinear/mask nearest interpolation is appropriate. Square resizing can erase small patches and distort geometry. The revision keeps one consistent square resize, audits native versus resized mask coverage, and measures coverage on the model grid. Any later tiling/letterboxing change needs its own validation and threshold selection. |
| Threshold | The saved run selected approximately 0.55 on validation and field inference used 0.55; the small rounding difference does not explain collapse. The revision loads the selected threshold from checkpoint-bound metadata and exports a wider validation-only sweep. Lowering the threshold against a failing field example is not an independent validation. |
| Training/checkpoints | Fine-tuning created a fresh “best” callback on the same file, permitting replacement of a better head checkpoint. The revision keeps both stages, compares validation loss, selects the better one, and verifies save/reload predictions. Every new run has a separate output directory. |
| Evaluation | Missing-negative metrics now remain missing rather than appearing as zero error. Confidence intervals resample groups. Independent labeled field evaluation rejects obvious development duplicates. Mean pixel certainty is explicitly distinguished from calibrated accuracy; low predictions do not establish absence. Coverage remains whole-photo area, not substrate-only area. |

## Use the corrected notebook

1. Open `EcoSignal_Coverage_v3_Corrected.ipynb` in a fresh Colab runtime and upload `Images.zip` and `Masks.zip`.
2. Set the explicit mask values: default black=0, lichen=255; indexed binary masks may require lichen=1. Check the mask coordinate convention for EXIF orientation. Review overlays for complete annotation of the intended lichen classes, then set `LABEL_REVIEW_COMPLETE=True`.
3. Supply `source_groups.csv` with one `stem,group_id` row per development image where groups identify the same source photo, specimen or site. The notebook writes a template if missing. Near-duplicate hash grouping alone does not establish site independence.
4. Run training and evaluation. New weights and reports go to a unique `coverage_v3_*` folder. Original Drive models and evaluation files are not overwritten.
5. Supply a separate `field_holdout.csv` (`stem,image_path,mask_path,group_id`) to measure field accuracy. Put representative field development images in training/validation first; reserve different specimens/sites for final field evaluation. Do not tune using the final holdout. Repeatedly inspected historical test data should be treated as development evidence.

All **56 original saved output bundles** are preserved exactly in the historical appendix, including plots, training logs and evaluation tables. Original sources are rendered as text so they cannot retrain or overwrite files during Run All. The unmodified `original.ipynb` is included as a separate backup; running output-only historical cells in a notebook frontend can clear their displayed outputs.

## Validation scope

See `validation_report.json` for executed checks. Tests cover notebook validity, exact output preservation, malformed masks, indexed masks, EXIF alignment, duplicate handling, grouped split isolation, metrics, threshold selection, grouped intervals, training/inference tensor parity, augmentation, model graph/scaling, save/reload, checkpoint loading and both training-stage callbacks. Model smoke tests use random initialization and synthetic inputs.

The original dataset archives, trained `.keras` checkpoint and original field-image file were not attached. Their saved plots and outputs were inspected. **No retraining, original-checkpoint inference reproduction, or measured field improvement is claimed.** Notebook changes correct the identifiable pipeline weaknesses; field generalization still requires representative annotations and independent evaluation.

References: [Keras MobileNetV2](https://keras.io/api/applications/mobilenet/mobilenet_models/), [Keras transfer learning](https://keras.io/guides/transfer_learning/), [MobileNetV2 graph source](https://github.com/keras-team/keras/blob/master/keras/src/applications/mobilenet_v2.py).
