from typing import Any
import numpy as np

def _quality(mask: np.ndarray, probability: np.ndarray) -> dict[str, Any]:
    import cv2
    h, w = mask.shape; coverage = float(100 * mask.mean()); reasons = []
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA] if count > 1 else np.array([], dtype=int)
    inside = probability[mask == 1]
    if inside.size:
        mean_inside = float(inside.mean()); p10 = float(np.percentile(inside, 10)); uncertain_inside = float(((inside > .35) & (inside < .65)).mean())
    else: mean_inside, p10, uncertain_inside = 0.0, 0.0, 1.0
    kernel = np.ones((5, 5), np.uint8); boundary = cv2.dilate(mask, kernel) - cv2.erode(mask, kernel)
    boundary_values = probability[boundary == 1]
    boundary_uncertain = float(((boundary_values > .35) & (boundary_values < .65)).mean()) if boundary_values.size else 1.0
    border = np.zeros_like(mask); border[:8] = 1; border[-8:] = 1; border[:, :8] = 1; border[:, -8:] = 1
    edge_fraction = float(((mask == 1) & (border == 1)).sum() / max(mask.sum(), 1))
    component_count = int(len(areas)); small_count = int((areas < 200).sum()); largest_ratio = float(areas.max() / max(areas.sum(), 1)) if areas.size else 0.0
    checks = [(coverage < 2, "coverage_too_low"), (coverage > 75, "coverage_too_high"), (mean_inside < .78, "mean_probability_low"),
              (p10 < .52, "low_confidence_regions_inside_mask"), (uncertain_inside > .25, "too_much_uncertainty_inside_mask"),
              (boundary_uncertain > .35, "uncertain_boundaries"), (component_count > 80, "too_fragmented"),
              (small_count > 40, "too_many_tiny_regions"), (component_count > 1 and largest_ratio < .25, "no_dominant_lichen_region"),
              (edge_fraction > .40, "mask_touches_edges_too_much")]
    reasons.extend(reason for failed, reason in checks if failed)
    label = "auto_accept_high_quality" if not reasons else "review_medium_quality" if len(reasons) <= 2 else "review_or_reject_low_quality"
    confidence = float(np.clip(mean_inside * (1 - .5 * uncertain_inside) * (1 - .35 * boundary_uncertain), 0, 1))
    return {"quality_label": label, "needs_manual_review": bool(reasons), "quality_reasons": reasons, "lichen_coverage_percent": coverage,
            "mean_prob_inside": mean_inside, "p10_prob_inside": p10, "uncertain_fraction_inside": uncertain_inside,
            "boundary_uncertain_fraction": boundary_uncertain, "component_count": component_count, "largest_component_ratio": largest_ratio,
            "small_component_count": small_count, "edge_touch_fraction": edge_fraction, "mask_pixels": int(mask.sum()),
            "image_pixels": int(h * w), "coverage_confidence": confidence}

