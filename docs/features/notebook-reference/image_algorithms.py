# Reference definitions only; imports/runtime supplied by the original notebook.
# Not executed by Sites. Original notebook SHA-256 is in sources.json.

def normalized_luminance(image_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

def sharpness(image_bgr: np.ndarray) -> float:
    return float(cv2.Laplacian(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())

def global_ssim(a: np.ndarray, b: np.ndarray) -> float:
    a, b = (a.astype(np.float64), b.astype(np.float64))
    c1, c2 = ((0.01 * 255) ** 2, (0.03 * 255) ** 2)
    ma, mb = (a.mean(), b.mean())
    va, vb = (a.var(), b.var())
    covariance = ((a - ma) * (b - mb)).mean()
    return float((2 * ma * mb + c1) * (2 * covariance + c2) / ((ma * ma + mb * mb + c1) * (va + vb + c2)))

def align_repeat_images(baseline_path: Path, current_path: Path) -> dict[str, Any]:
    base = load_cv_image(baseline_path)
    current = load_cv_image(current_path)
    current = cv2.resize(current, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_AREA)
    bg, cg = (normalized_luminance(base), normalized_luminance(current))
    orb = cv2.ORB_create(nfeatures=3500, scaleFactor=1.2, nlevels=8)
    key1, desc1 = orb.detectAndCompute(bg, None)
    key2, desc2 = orb.detectAndCompute(cg, None)
    if desc1 is None or desc2 is None or len(key1) < 12 or (len(key2) < 12):
        return {'decision': 'retake_required', 'comparability_score': 0.0, 'reason': 'Insufficient stable visual features for same-site alignment.', 'metrics': {'keypoints_baseline': len(key1), 'keypoints_current': len(key2)}}
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(desc2, desc1, k=2)
    good = [m for m, n in pairs if m.distance < 0.72 * n.distance]
    if len(good) < 12:
        return {'decision': 'retake_required', 'comparability_score': 0.0, 'reason': 'Too few consistent matches; reproduce the original framing.', 'metrics': {'good_matches': len(good)}}
    src = np.float32([key2[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([key1[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    homography, inliers = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    if homography is None or inliers is None:
        return {'decision': 'retake_required', 'comparability_score': 0.0, 'reason': 'RANSAC could not establish stable alignment.', 'metrics': {'good_matches': len(good)}}
    aligned = cv2.warpPerspective(current, homography, (base.shape[1], base.shape[0]))
    valid = cv2.warpPerspective(np.full(current.shape[:2], 255, np.uint8), homography, (base.shape[1], base.shape[0])) > 0
    overlap = float(valid.mean())
    inlier_ratio = float(inliers.ravel().mean())
    ys, xs = np.where(valid)
    if len(xs) < 100:
        return {'decision': 'retake_required', 'comparability_score': 0.0, 'reason': 'Aligned overlap is too small.', 'metrics': {'overlap_fraction': overlap}}
    x0, x1, y0, y1 = (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)
    ssim = global_ssim(normalized_luminance(base)[y0:y1, x0:x1], normalized_luminance(aligned)[y0:y1, x0:x1])
    exposure_difference = abs(float(cv2.cvtColor(base, cv2.COLOR_BGR2GRAY).mean()) - float(cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)[valid].mean())) / 255
    sharp_ratio = min(sharpness(base), sharpness(aligned)) / max(sharpness(base), sharpness(aligned), 1e-06)
    components = {'ransac_inlier_ratio': float(np.clip(inlier_ratio / 0.65, 0, 1)), 'structural_similarity': float(np.clip((ssim - 0.15) / 0.7, 0, 1)), 'exposure_consistency': float(np.clip(1 - exposure_difference / 0.35, 0, 1)), 'overlap_fraction': float(np.clip(overlap / 0.85, 0, 1)), 'sharpness_consistency': float(np.clip(sharp_ratio, 0, 1))}
    score = 0.32 * components['ransac_inlier_ratio'] + 0.3 * components['structural_similarity'] + 0.16 * components['exposure_consistency'] + 0.12 * components['overlap_fraction'] + 0.1 * components['sharpness_consistency']
    decision = 'retake_required' if overlap < 0.35 else 'accepted' if score >= 0.72 else 'caution' if score >= 0.52 else 'retake_required'
    reason = {'accepted': 'Images are sufficiently comparable for screening-level change analysis.', 'caution': 'Images can be compared only with increased uncertainty.', 'retake_required': 'Framing or visual conditions differ too much for a defensible comparison.'}[decision]
    return {'decision': decision, 'comparability_score': round(float(score), 4), 'reason': reason, 'metrics': {**{k: round(v, 4) for k, v in components.items()}, 'raw_ssim': round(ssim, 4), 'raw_inlier_ratio': round(inlier_ratio, 4), 'raw_overlap_fraction': round(overlap, 4), 'exposure_difference': round(exposure_difference, 4), 'good_matches': len(good)}, '_aligned_image': aligned, '_baseline_image': base}

def coverage_change_interval(previous: float, current: float, comparability_score: float) -> dict[str, Any]:
    delta = float(current - previous)
    residual_sigma = COVERAGE_HELDOUT_MAE_PP * math.sqrt(math.pi / 2)
    base_half_width = 1.96 * math.sqrt(2) * residual_sigma
    half_width = base_half_width / max(float(comparability_score), 0.45)
    lower, upper = (delta - half_width, delta + half_width)
    status = 'increase_supported' if lower > 0 else 'decrease_supported' if upper < 0 else 'no_reliable_change_detected'
    return {'coverage_delta_pp': round(delta, 2), 'approx_95_interval_pp': [round(lower, 2), round(upper, 2)], 'change_status': status, 'mae_basis_pp': COVERAGE_HELDOUT_MAE_PP, 'interval_method': 'held-out-MAE normal approximation, comparability-inflated; screening only'}

@dataclass(frozen=True)
class CaptureThresholds:
    min_short_side: int = 384
    min_total_pixels: int = 600000
    min_blur_variance: float = 85.0
    min_mean_luminance: float = 0.18
    max_mean_luminance: float = 0.86
    min_robust_contrast: float = 0.2
    max_underexposed_fraction: float = 0.22
    max_overexposed_fraction: float = 0.18
    min_lichen_fraction: float = 0.08
    max_lichen_fraction: float = 0.92
    max_centroid_offset: float = 0.34
    max_border_touch_sides: int = 3

def base_capture_metrics(image: np.ndarray) -> dict[str, float]:
    h, w = image.shape[:2]
    scale = min(1.0, 900 / max(h, w))
    stable = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA) if scale < 1 else image
    gray = cv2.cvtColor(stable, cv2.COLOR_RGB2GRAY)
    luma = gray.astype(np.float32) / 255
    p05, p95 = np.percentile(luma, [5, 95])
    hsv = cv2.cvtColor(stable, cv2.COLOR_RGB2HSV)
    return {'width': w, 'height': h, 'blur_variance': float(cv2.Laplacian(gray, cv2.CV_64F).var()), 'mean_luminance': float(luma.mean()), 'robust_contrast': float(p95 - p05), 'underexposed_fraction': float((luma < 0.05).mean()), 'overexposed_fraction': float((luma > 0.98).mean()), 'mean_saturation': float((hsv[..., 1].astype(np.float32) / 255).mean())}

def mask_framing_metrics(mask: np.ndarray) -> dict[str, Any]:
    binary = (mask > 0).astype(np.uint8)
    fraction = float(binary.mean())
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)
    if count <= 1 or binary.sum() == 0:
        return {'lichen_fraction': fraction, 'largest_component_fraction': 0.0, 'centroid_offset': 1.0, 'border_touch_sides': 0}
    component = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    largest = labels == component
    cx, cy = centroids[component]
    center_x, center_y = ((mask.shape[1] - 1) / 2, (mask.shape[0] - 1) / 2)
    offset = math.hypot(cx - center_x, cy - center_y) / max(math.hypot(center_x, center_y), 1)
    sides = int(largest[0, :].any()) + int(largest[-1, :].any()) + int(largest[:, 0].any()) + int(largest[:, -1].any())
    return {'lichen_fraction': fraction, 'largest_component_fraction': float(largest.sum() / max(binary.sum(), 1)), 'centroid_offset': float(offset), 'border_touch_sides': sides}