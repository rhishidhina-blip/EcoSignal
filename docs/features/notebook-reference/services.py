"""Model-independent services shared by EcoSignal Features 8, 9, 14, and 16."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Protocol

from PIL import Image, ImageFilter, ImageStat
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditEvent, utc_now


ERROR_CATALOG: dict[str, dict[str, Any]] = {
    "UNSUPPORTED_FILE_TYPE": {"severity": "error", "retry_allowed": True},
    "IMAGE_CORRUPTED": {"severity": "error", "retry_allowed": True},
    "IMAGE_TOO_SMALL": {"severity": "error", "retry_allowed": True},
    "IMAGE_TOO_BLURRY": {"severity": "error", "retry_allowed": True},
    "IMAGE_TOO_DARK": {"severity": "error", "retry_allowed": True},
    "IMAGE_OVEREXPOSED": {"severity": "error", "retry_allowed": True},
    "DUPLICATE_IMAGE": {"severity": "error", "retry_allowed": False},
    "MODEL_NOT_AVAILABLE": {"severity": "error", "retry_allowed": False},
    "MODEL_TIMEOUT": {"severity": "error", "retry_allowed": True},
    "MODEL_INTERNAL_ERROR": {"severity": "error", "retry_allowed": True},
    "NO_LICHEN_DETECTED": {"severity": "error", "retry_allowed": True},
    "PREDICTION_LOW_CONFIDENCE": {"severity": "warning", "retry_allowed": False},
    "GROWTH_FORM_REJECTED": {"severity": "warning", "retry_allowed": True},
    "CHLOROSIS_UNAVAILABLE": {"severity": "warning", "retry_allowed": False},
    "NITROPHYTE_ACIDOPHYTE_UNKNOWN": {"severity": "warning", "retry_allowed": False},
    "FEATURE_SCHEMA_MISMATCH": {"severity": "error", "retry_allowed": False},
    "LOCATION_MISSING": {"severity": "warning", "retry_allowed": True},
    "LOCATION_UNSUPPORTED": {"severity": "error", "retry_allowed": False},
    "GEOSPATIAL_LOOKUP_FAILED": {"severity": "warning", "retry_allowed": True},
    "MAP_CELL_NOT_FOUND": {"severity": "warning", "retry_allowed": True},
    "ASSET_UPLOAD_FAILED": {"severity": "error", "retry_allowed": True},
    "SAMPLE_NOT_FOUND": {"severity": "error", "retry_allowed": False},
    "DATABASE_WRITE_FAILED": {"severity": "error", "retry_allowed": True},
    "LOW_LIGHT_WARNING": {"severity": "warning", "retry_allowed": True},
    "MISSING_OPTIONAL_METADATA": {"severity": "warning", "retry_allowed": True},
    "LOW_GROWTH_FORM_CONFIDENCE": {"severity": "warning", "retry_allowed": False},
}


def issue(code: str, message: str, *, details: dict[str, Any] | None = None,
          status: str | None = None) -> dict[str, Any]:
    properties = ERROR_CATALOG.get(code, {"severity": "error", "retry_allowed": False})
    return {
        "status": status or ("warning" if properties["severity"] == "warning" else "failed"),
        "code": code,
        "message": message,
        "severity": properties["severity"],
        "retry_allowed": properties["retry_allowed"],
        "details": details or {},
    }


def append_event(session: Session, event_type: str, entity_type: str, entity_id: str,
                 *, sample_id: str | None = None, actor_id: str | None = None,
                 payload: dict[str, Any] | None = None) -> AuditEvent:
    """Append a hash-chained event; callers commit it with the related transaction."""
    previous = session.scalar(select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(1))
    created_at = utc_now()
    canonical = json.dumps({
        "event_type": event_type, "entity_type": entity_type, "entity_id": entity_id,
        "sample_id": sample_id, "actor_id": actor_id, "payload": payload or {},
        "previous_event_hash": previous.event_hash if previous else None,
    }, sort_keys=True, separators=(",", ":"), default=str)
    event = AuditEvent(
        event_type=event_type, entity_type=entity_type, entity_id=entity_id,
        sample_id=sample_id, actor_id=actor_id, payload_json=payload or {},
        previous_event_hash=previous.event_hash if previous else None,
        event_hash=sha256(canonical.encode("utf-8")).hexdigest(), created_at=created_at,
    )
    session.add(event)
    session.flush()
    return event


class ModelAdapter(Protocol):
    model_type: str
    model_version: str
    is_placeholder: bool

    def predict(self, image_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...


class QualityService:
    quality_version = "image_quality_v0_configurable"

    def __init__(self, thresholds: dict[str, float] | None = None):
        defaults = {
            "min_width": float(os.getenv("ECOSIGNAL_MIN_IMAGE_WIDTH", "64")),
            "min_height": float(os.getenv("ECOSIGNAL_MIN_IMAGE_HEIGHT", "64")),
            "min_blur_score": float(os.getenv("ECOSIGNAL_MIN_BLUR_SCORE", "8")),
            "min_brightness": float(os.getenv("ECOSIGNAL_MIN_BRIGHTNESS", "0.10")),
            "max_brightness": float(os.getenv("ECOSIGNAL_MAX_BRIGHTNESS", "0.92")),
            "max_overexposed_fraction": float(os.getenv("ECOSIGNAL_MAX_OVEREXPOSED", "0.80")),
            "min_contrast": float(os.getenv("ECOSIGNAL_MIN_CONTRAST", "0.08")),
        }
        defaults.update(thresholds or {})
        self.thresholds = defaults

    def assess(self, image_path: str | Path, metadata_complete: bool = True) -> dict[str, Any]:
        with Image.open(image_path) as image:
            gray = image.convert("L")
            width, height = gray.size
            stats = ImageStat.Stat(gray)
            brightness = stats.mean[0] / 255.0
            contrast = stats.stddev[0] / 255.0
            edges = gray.filter(ImageFilter.FIND_EDGES)
            blur_score = ImageStat.Stat(edges).var[0]
            histogram = gray.histogram()
            overexposed_fraction = sum(histogram[245:]) / max(1, width * height)

        metrics = {
            "width": width, "height": height, "blur_score": round(blur_score, 4),
            "brightness": round(brightness, 4), "contrast": round(contrast, 4),
            "overexposed_fraction": round(overexposed_fraction, 4),
            "metadata_completeness": 1.0 if metadata_complete else 0.0,
        }
        blockers: list[str] = []
        warnings: list[str] = []
        t = self.thresholds
        if width < t["min_width"] or height < t["min_height"]: blockers.append("IMAGE_TOO_SMALL")
        if blur_score < t["min_blur_score"]: blockers.append("IMAGE_TOO_BLURRY")
        if brightness < t["min_brightness"]: blockers.append("IMAGE_TOO_DARK")
        if brightness > t["max_brightness"] or overexposed_fraction > t["max_overexposed_fraction"]: blockers.append("IMAGE_OVEREXPOSED")
        if contrast < t["min_contrast"]: warnings.append("LOW_CONTRAST")
        if not metadata_complete: warnings.append("MISSING_OPTIONAL_METADATA")

        component_scores = [
            min(1.0, width / max(1.0, t["min_width"])),
            min(1.0, height / max(1.0, t["min_height"])),
            min(1.0, blur_score / max(1.0, t["min_blur_score"] * 2)),
            max(0.0, 1.0 - abs(brightness - .5) / .5),
            min(1.0, contrast / max(.01, t["min_contrast"] * 2)),
            1.0 if metadata_complete else .5,
        ]
        quality_score = round(sum(component_scores) / len(component_scores), 4)
        decision = "rejected" if blockers else ("accepted_with_warning" if warnings else "accepted")
        return {
            "quality_score": quality_score, "decision": decision, "metrics": metrics,
            "warnings": blockers + warnings, "thresholds": dict(t),
            "quality_version": self.quality_version,
        }


DEFAULT_CONFIDENCE_WEIGHTS = {
    "image_quality": .20, "coverage": .20, "growth_form": .15,
    "chlorosis": .10, "geospatial_completeness": .15,
    "risk_engine": .15, "feature_completeness": .05,
}


def aggregate_confidence(components: dict[str, float | None],
                         weights: dict[str, float] | None = None) -> dict[str, Any]:
    selected = dict(weights or DEFAULT_CONFIDENCE_WEIGHTS)
    unknown = set(components) - set(selected)
    if unknown:
        raise ValueError(f"Unknown confidence components: {', '.join(sorted(unknown))}")
    if any(value is not None and not 0 <= value <= 1 for value in components.values()):
        raise ValueError("Confidence components must be null or between 0 and 1")
    present = {key: float(value) for key, value in components.items() if value is not None and key in selected}
    denominator = sum(selected[key] for key in present)
    overall = None if denominator == 0 else round(sum(present[key] * selected[key] for key in present) / denominator, 4)
    limitations = [f"{key.replace('_', ' ').title()} confidence unavailable" for key in selected if components.get(key) is None]
    return {"overall_confidence": overall, "weights": selected, "limitations": limitations}
