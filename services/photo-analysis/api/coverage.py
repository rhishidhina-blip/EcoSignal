from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps
from .coverage_quality import _quality

VERSION = "coverage_mobilenetv2_unet_320_v2_t065"
EXPECTED_SHA256 = "0496f79a349de607d43f6e3db3f05fe542e7d76ee13e46bf7b352feae7db3133"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "lichen_coverage_v2.keras"
INPUT_SIZE = 320
THRESHOLD = 0.65  # Explicitly supplied by the model owner on October 24, 2026.


def _sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


@lru_cache(maxsize=1)
def _load(path: str):
    import tensorflow as tf
    # Inference does not need the custom training losses or metrics.
    model = tf.keras.models.load_model(path, compile=False, safe_mode=True)
    if model.input_shape != (None, INPUT_SIZE, INPUT_SIZE, 3):
        raise ValueError(f"Unexpected coverage input shape: {model.input_shape}")
    if model.output_shape != (None, INPUT_SIZE, INPUT_SIZE, 1):
        raise ValueError(f"Unexpected coverage output shape: {model.output_shape}")
    return model


def _probabilities(model, image: Image.Image) -> np.ndarray:
    import tensorflow as tf
    # The saved model includes Rescaling(2, offset=-1). Supply RGB in [0,1].
    rgb = tf.convert_to_tensor(np.asarray(image), dtype=tf.float32) / 255.0
    batch = tf.image.resize(rgb, (INPUT_SIZE, INPUT_SIZE), method="bilinear")[None, ...]
    values = np.asarray(model(batch, training=False), dtype=np.float32)
    if values.shape != (1, INPUT_SIZE, INPUT_SIZE, 1):
        raise ValueError("Coverage model returned an unexpected tensor shape")
    probability = values[0, :, :, 0]
    if not np.isfinite(probability).all() or probability.min() < 0 or probability.max() > 1:
        raise ValueError("Coverage model returned invalid probabilities")
    return probability


def _binary_mask(probability: np.ndarray) -> np.ndarray:
    return (probability >= THRESHOLD).astype(np.uint8)


def predict(*, image_path: str, context: dict[str, Any]) -> dict[str, Any]:
    path = DEFAULT_MODEL_PATH
    if not path.is_file():
        return {"status": "unavailable", "version": VERSION, "warnings": ["Coverage model file is missing"]}
    checksum = _sha256(path)
    if checksum != EXPECTED_SHA256:
        return {"status": "failed", "version": VERSION, "warnings": ["Coverage model checksum does not match the supplied replacement"]}
    model = _load(str(path.resolve()))
    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    rgb = np.asarray(image)
    w, h = image.size
    probability = _probabilities(model, image)
    native_mask = _binary_mask(probability)
    # Measure the model-resolution mask, matching the training evaluation contract.
    # Resize labels (nearest neighbor) only for display; do not re-threshold smoothing.
    mask = np.asarray(Image.fromarray(native_mask * 255).resize((w, h), Image.Resampling.NEAREST))
    qa = _quality(native_mask, probability)
    artifact_dir = Path(context["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    mask_path = artifact_dir / "coverage_mask.png"
    overlay_path = artifact_dir / "coverage_overlay.png"
    probability_path = artifact_dir / "coverage_probability.png"
    Image.fromarray(mask).save(mask_path)
    colored = rgb.copy()
    colored[mask > 0] = [255, 70, 70]
    Image.fromarray(np.clip(.68 * rgb.astype(np.float32) + .32 * colored, 0, 255).astype(np.uint8)).save(overlay_path)
    Image.fromarray(np.rint(probability * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR).save(probability_path)
    warnings = [f"Coverage mask QA (legacy, uncalibrated for v2): {reason}" for reason in qa["quality_reasons"]]
    warnings.append("Coverage and confidence diagnostics require review; this replacement has not been independently validated on these field photos.")
    return {
        "status": "rejected_low_confidence" if qa["quality_label"] == "review_or_reject_low_quality" else "available",
        "value": {"coverage_percent": float(native_mask.mean() * 100)},
        "confidence": qa["coverage_confidence"], "version": VERSION, "warnings": warnings,
        "artifacts": {"coverage_mask": str(mask_path), "coverage_overlay": str(overlay_path), "coverage_probability": str(probability_path)},
        "details": {**qa, "needs_manual_review": True, "checkpoint_sha256": checksum,
                    "input_size": INPUT_SIZE, "threshold": THRESHOLD, "threshold_source": "model_owner_explicit_instruction_2026-10-24",
                    "input_preprocessing": "RGB [0,1]; bilinear resize; [-1,1] rescaling inside model",
                    "coverage_basis": "thresholded native 320x320 mask over the entire photograph",
                    "postprocessing": "none; nearest-neighbor display mask", "confidence_calibrated": False,
                    "quality_gate": "legacy heuristic retained, not validated for replacement model"}}
