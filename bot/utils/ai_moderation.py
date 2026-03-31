"""AI moderation pipeline for event verification.

Analyzes uploaded photos and geolocation to auto-approve or flag for coordinator review.

Scoring system (0–100 points):
  Block 1 — EXIF timestamp ≤ 2h              25 pts (proportional across photos)
  Block 2 — EXIF GPS matches submitted loc    20 pts (proportional)
  Block 3 — Face detected (selfie check)      15 pts + 5 bonus if ≥3 faces
  Block 4 — Blur: Laplacian variance > 80     10 pts (full/half/none)
  Block 5 — Resolution ≥ 320×240              5 pts
  Block 6 — Photo count 2–3                   5 pts
  ─────────────────────────────────────────────────────
  Max without bonus                           80 pts
  Max with audience bonus                     85 pts

  ≥ 80 → auto-approved
  50–79 → coordinator queue
  < 50  → coordinator queue + high_risk flag
"""
import logging

import cv2

from bot.utils.exif import extract_exif, is_recent
from bot.utils.face import detect_faces
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


def run_moderation(
    photo_paths: list[str],
    lat: float = None,
    lon: float = None,
    title: str = "",
    description: str = "",
    demo_mode: bool = True,
) -> dict:
    """
    Run full moderation pipeline.

    Returns:
        {
            "approved": bool,
            "score": int (0–100),
            "confidence_percent": int (0–100),
            "reasons": list[str],
            "details": dict,
            "high_risk": bool,
        }
    """
    if not photo_paths:
        return {
            "approved": False,
            "score": 0,
            "confidence_percent": 0,
            "reasons": ["Фотографии не загружены"],
            "details": {},
            "high_risk": True,
        }

    score = 0
    reasons: list[str] = []
    details: dict = {}
    n = len(photo_paths)

    # ── Block 6: Photo count (5 pts) ────────────────────────────────────────
    if 2 <= n <= 3:
        score += 5
    else:
        reasons.append(f"Загружено {n} фото (требуется 2–3)")
    details["photo_count"] = {"count": n, "ok": 2 <= n <= 3}

    # ── Per-photo checks ─────────────────────────────────────────────────────
    exif_time_pass = 0
    exif_gps_pass = 0
    exif_gps_checked = 0
    blur_pass = 0
    res_pass = 0
    has_face = False
    max_face_count = 0

    for i, path in enumerate(photo_paths):
        photo_num = i + 1

        # Block 1: EXIF timestamp
        exif = extract_exif(path)
        if exif["datetime"]:
            if is_recent(exif["datetime"], max_hours=2):
                exif_time_pass += 1
            else:
                reasons.append(f"Фото #{photo_num}: снято более 2 часов назад")
        else:
            reasons.append(f"Фото #{photo_num}: нет EXIF-метки времени")

        # Block 2: EXIF GPS vs submitted location
        if lat is not None and lon is not None:
            if exif["lat"] is not None and exif["lon"] is not None:
                exif_gps_checked += 1
                dist = haversine(exif["lat"], exif["lon"], lat, lon)
                if dist <= 500:
                    exif_gps_pass += 1
                else:
                    reasons.append(
                        f"Фото #{photo_num}: GPS в EXIF отличается на {dist:.0f} м "
                        f"от указанной точки (макс. 500 м)"
                    )
            else:
                reasons.append(f"Фото #{photo_num}: нет GPS в EXIF")
        else:
            # No submitted location — skip GPS check, give benefit of the doubt
            exif_gps_pass += 1
            exif_gps_checked += 1

        # Block 4: Blur
        is_sharp, blur_var = analyze_blur(path)
        if is_sharp:
            blur_pass += 1
        else:
            reasons.append(f"Фото #{photo_num}: размытое (резкость: {blur_var:.0f}, мин. 80)")

        # Block 5: Resolution
        res_ok, res_size = analyze_resolution(path)
        if res_ok:
            res_pass += 1
        else:
            reasons.append(f"Фото #{photo_num}: слишком малое разрешение {res_size[0]}×{res_size[1]}")

        # Block 3: Face detection
        face = detect_faces(path)
        if face["found"]:
            has_face = True
            max_face_count = max(max_face_count, face["count"])

    # ── Block 1: EXIF timestamp score (25 pts, proportional) ────────────────
    block1 = round((exif_time_pass / n) * 25)
    score += block1
    details["exif_timestamp"] = {"passed": exif_time_pass, "total": n, "pts": block1}

    # ── Block 2: EXIF GPS score (20 pts, proportional) ──────────────────────
    if exif_gps_checked > 0:
        block2 = round((exif_gps_pass / exif_gps_checked) * 20)
    else:
        block2 = 0
    score += block2
    details["exif_gps"] = {"passed": exif_gps_pass, "checked": exif_gps_checked, "pts": block2}

    # ── Block 3: Face detection (15 pts + 5 audience bonus) ─────────────────
    if has_face:
        face_pts = 15
        if max_face_count >= 3:
            face_pts += 5
            reasons_face = f"Обнаружено лиц: {max_face_count} (бонус за аудиторию)"
        else:
            reasons_face = f"Обнаружено лиц: {max_face_count}"
        score += face_pts
        details["faces"] = {"found": True, "max_count": max_face_count, "pts": face_pts, "note": reasons_face}
    else:
        reasons.append("Селфи не обнаружено — на фотографиях не найдено лиц")
        details["faces"] = {"found": False, "max_count": 0, "pts": 0}

    # ── Block 4: Blur (10 pts: all sharp=10, half=5, less=0) ────────────────
    blur_ratio = blur_pass / n
    if blur_ratio >= 1.0:
        block4 = 10
    elif blur_ratio >= 0.5:
        block4 = 5
    else:
        block4 = 0
    score += block4
    details["blur"] = {"sharp": blur_pass, "total": n, "pts": block4}

    # ── Block 5: Resolution (5 pts: all pass=5, else=0) ─────────────────────
    block5 = 5 if res_pass == n else 0
    score += block5
    details["resolution"] = {"ok": res_pass == n, "passed": res_pass, "total": n, "pts": block5}

    details["total_score"] = score

    # ── Verdict ──────────────────────────────────────────────────────────────
    approved = score >= 80
    high_risk = score < 50

    if approved:
        verdict = [f"✅ Авто-одобрено (AI score: {score}/100)"]
    elif high_risk:
        verdict = [f"⚠️ Высокий риск (score: {score}/100) — отправлено координатору"]
    else:
        verdict = [f"📋 Отправлено на проверку координатору (score: {score}/100)"]

    if reasons:
        verdict += reasons

    return {
        "approved": approved,
        "score": score,
        "confidence_percent": score,
        "reasons": verdict,
        "details": details,
        "high_risk": high_risk,
    }
