"""AI moderation pipeline for event verification.

Analyzes uploaded photos and geolocation to auto-approve or flag for coordinator review.
"""
import json
import logging

import cv2

from bot.utils.face import detect_face
from bot.utils.geo import haversine

logger = logging.getLogger(__name__)


def analyze_blur(image_path: str, threshold: float = 80.0) -> tuple[bool, float]:
    """Check if image is blurry. Returns (is_sharp, variance)."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False, 0.0
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance >= threshold, variance
    except Exception as e:
        logger.error("Blur analysis error: %s", e)
        return False, 0.0


def analyze_resolution(image_path: str, min_w: int = 320, min_h: int = 240) -> tuple[bool, tuple]:
    """Check minimum resolution."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False, (0, 0)
        h, w = img.shape[:2]
        return w >= min_w and h >= min_h, (w, h)
    except Exception as e:
        logger.error("Resolution analysis error: %s", e)
        return False, (0, 0)


def analyze_geolocation(lat: float, lon: float) -> dict:
    """Validate that geolocation is plausible (not null island, within Earth bounds)."""
    reasons = []
    valid = True

    if lat is None or lon is None:
        return {"valid": False, "reasons": ["Геолокация не указана"]}

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        valid = False
        reasons.append("Координаты вне допустимого диапазона")

    if abs(lat) < 0.01 and abs(lon) < 0.01:
        valid = False
        reasons.append("Координаты указывают на нулевой остров (0,0)")

    return {"valid": valid, "reasons": reasons}


def analyze_text(title: str, description: str = "") -> dict:
    """Validate event title and description quality."""
    reasons = []
    score = 1.0

    if len(title.strip()) < 3:
        reasons.append("Название слишком короткое (мин. 3 символа)")
        score -= 0.5

    if len(title.strip()) > 200:
        reasons.append("Название слишком длинное")
        score -= 0.2

    if title.isupper() and len(title) > 5:
        reasons.append("Название написано КАПСОМ")
        score -= 0.1

    return {"score": max(score, 0), "reasons": reasons}


def run_moderation(
    photo_paths: list[str],
    lat: float = None,
    lon: float = None,
    title: str = "",
    description: str = "",
    demo_mode: bool = True,
) -> dict:
    """
    Run full AI moderation pipeline.

    Returns:
        {
            "approved": bool,
            "score": float (0-1),
            "reasons": list[str],  # rejection reasons
            "details": dict,       # per-check results
        }
    """
    reasons = []
    details = {}
    total_score = 0.0
    checks = 0

    photo_scores = []
    has_any_face = False
    for i, path in enumerate(photo_paths):
        is_sharp, blur_var = analyze_blur(path)
        res_ok, res_size = analyze_resolution(path)
        has_face = detect_face(path)

        if has_face:
            has_any_face = True

        photo_score = 0.0
        if is_sharp:
            photo_score += 0.4
        else:
            reasons.append(f"Фото #{i+1}: размытое (резкость: {blur_var:.0f})")
        if res_ok:
            photo_score += 0.3
        else:
            reasons.append(f"Фото #{i+1}: слишком маленькое разрешение {res_size}")
        if has_face:
            photo_score += 0.3

        photo_scores.append(photo_score)

    if photo_paths:
        avg_photo = sum(photo_scores) / len(photo_scores)
        total_score += avg_photo
        checks += 1
        details["photos"] = {
            "count": len(photo_paths),
            "avg_score": round(avg_photo, 2),
            "has_face": has_any_face,
        }
    else:
        reasons.append("Фотографии не загружены")
        details["photos"] = {"count": 0, "avg_score": 0, "has_face": False}

    geo = analyze_geolocation(lat, lon)
    if geo["valid"]:
        total_score += 1.0
    else:
        reasons.extend(geo["reasons"])
    checks += 1
    details["geo"] = geo

    text = analyze_text(title, description)
    total_score += text["score"]
    checks += 1
    if text["reasons"]:
        reasons.extend(text["reasons"])
    details["text"] = text

    final_score = total_score / max(checks, 1)

    # Decision: approve if score >= 0.6 (lenient for demo)
    threshold = 0.4 if demo_mode else 0.6
    approved = final_score >= threshold and len(photo_paths) > 0

    # In demo mode, be more lenient
    if demo_mode and len(photo_paths) > 0:
        approved = True
        if not reasons:
            reasons = []

    return {
        "approved": approved,
        "score": round(final_score, 2),
        "reasons": reasons,
        "details": details,
    }
