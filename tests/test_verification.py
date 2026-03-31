"""Tests for the verification pipeline (face detection, EXIF, scoring)."""
import os
import struct
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import cv2
import numpy as np
import pytest
from PIL import Image

from bot.utils.ai_moderation import (
    analyze_blur,
    analyze_resolution,
    run_moderation,
)
from bot.utils.exif import extract_exif, is_recent
from bot.utils.face import detect_face, detect_faces
from bot.utils.geo import haversine, is_location_match


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_image(w=640, h=480, noise=True) -> str:
    """Create a valid JPEG temp file. Returns path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    if noise:
        # High-frequency noise → sharp image
        arr = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    else:
        # Solid color → blurry (Laplacian variance ≈ 0)
        arr = np.full((h, w, 3), 128, dtype=np.uint8)
    cv2.imwrite(tmp.name, arr)
    return tmp.name


def make_tiny_image() -> str:
    """Create a 100×80 JPEG (below 320×240 minimum)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    arr = np.random.randint(0, 255, (80, 100, 3), dtype=np.uint8)
    cv2.imwrite(tmp.name, arr)
    return tmp.name


def make_image_with_exif(dt: datetime = None, lat: float = None, lon: float = None) -> str:
    """Create JPEG with EXIF datetime and optionally GPS coords."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()

    img = Image.new("RGB", (640, 480), color=(100, 150, 200))

    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}

    if dt:
        import piexif
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt.strftime("%Y:%m:%d %H:%M:%S").encode()

    if lat is not None and lon is not None:
        import piexif

        def to_rational(val):
            val = abs(val)
            deg = int(val)
            minutes = int((val - deg) * 60)
            seconds = round(((val - deg) * 60 - minutes) * 60 * 100)
            return [(deg, 1), (minutes, 1), (seconds, 100)]

        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b"N" if lat >= 0 else b"S"
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = to_rational(lat)
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b"E" if lon >= 0 else b"W"
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = to_rational(lon)

    try:
        import piexif
        exif_bytes = piexif.dump(exif_dict)
        img.save(tmp.name, exif=exif_bytes)
    except ImportError:
        img.save(tmp.name)

    return tmp.name


# ── geo.py ────────────────────────────────────────────────────────────────────

class TestHaversine:
    def test_same_point(self):
        assert haversine(55.75, 37.62, 55.75, 37.62) == pytest.approx(0.0)

    def test_moscow_spb(self):
        # Moscow → Saint Petersburg ≈ 634 km
        dist = haversine(55.7558, 37.6173, 59.9386, 30.3141)
        assert 620_000 < dist < 650_000

    def test_short_distance(self):
        # ~100 m north of Moscow center
        dist = haversine(55.7558, 37.6173, 55.7567, 37.6173)
        assert dist < 200

    def test_is_location_match_within(self):
        assert is_location_match(55.75, 37.62, 55.751, 37.62) is True

    def test_is_location_match_outside(self):
        # ~1 km away
        assert is_location_match(55.75, 37.62, 55.76, 37.62) is False

    def test_none_coords(self):
        assert is_location_match(None, None, 55.75, 37.62) is False


# ── exif.py ───────────────────────────────────────────────────────────────────

class TestIsRecent:
    def test_just_now(self):
        assert is_recent(datetime.now()) is True

    def test_one_hour_ago(self):
        assert is_recent(datetime.now() - timedelta(hours=1)) is True

    def test_exactly_two_hours(self):
        assert is_recent(datetime.now() - timedelta(hours=2, seconds=1)) is False

    def test_yesterday(self):
        assert is_recent(datetime.now() - timedelta(days=1)) is False

    def test_none(self):
        assert is_recent(None) is False


class TestExtractExif:
    def test_no_exif_returns_none_fields(self):
        path = make_image()
        try:
            result = extract_exif(path)
            assert result["datetime"] is None
            assert result["lat"] is None
            assert result["lon"] is None
        finally:
            os.unlink(path)

    def test_with_datetime_exif(self):
        try:
            import piexif
        except ImportError:
            pytest.skip("piexif not installed")

        dt = datetime.now() - timedelta(minutes=30)
        path = make_image_with_exif(dt=dt)
        try:
            result = extract_exif(path)
            assert result["datetime"] is not None
            diff = abs((result["datetime"] - dt).total_seconds())
            assert diff < 2
        finally:
            os.unlink(path)

    def test_with_gps_exif(self):
        try:
            import piexif
        except ImportError:
            pytest.skip("piexif not installed")

        path = make_image_with_exif(lat=55.7558, lon=37.6173)
        try:
            result = extract_exif(path)
            assert result["lat"] is not None
            assert result["lon"] is not None
            assert abs(result["lat"] - 55.7558) < 0.001
            assert abs(result["lon"] - 37.6173) < 0.001
        finally:
            os.unlink(path)


# ── face.py ───────────────────────────────────────────────────────────────────

class TestDetectFaces:
    def test_no_face_in_noise(self):
        path = make_image(noise=True)
        try:
            result = detect_faces(path)
            assert isinstance(result, dict)
            assert "found" in result
            assert "count" in result
            assert "confidence" in result
            assert isinstance(result["found"], bool)
            assert result["count"] >= 0
        finally:
            os.unlink(path)

    def test_missing_file(self):
        result = detect_faces("/nonexistent/path/image.jpg")
        assert result["found"] is False
        assert result["count"] == 0

    def test_detect_face_wrapper_returns_bool(self):
        path = make_image()
        try:
            result = detect_face(path)
            assert isinstance(result, bool)
        finally:
            os.unlink(path)

    def test_detect_face_consistent_with_detect_faces(self):
        path = make_image()
        try:
            faces = detect_faces(path)
            face = detect_face(path)
            assert face == faces["found"]
        finally:
            os.unlink(path)


# ── ai_moderation.py ──────────────────────────────────────────────────────────

class TestAnalyzeBlur:
    def test_sharp_image(self):
        path = make_image(noise=True)
        try:
            is_sharp, variance = analyze_blur(path)
            assert bool(is_sharp) is True
            assert variance > 80
        finally:
            os.unlink(path)

    def test_blurry_image(self):
        path = make_image(noise=False)
        try:
            is_sharp, variance = analyze_blur(path)
            assert bool(is_sharp) is False
            assert variance < 80
        finally:
            os.unlink(path)

    def test_missing_file(self):
        is_sharp, variance = analyze_blur("/nonexistent.jpg")
        assert is_sharp is False
        assert variance == 0.0


class TestAnalyzeResolution:
    def test_ok_resolution(self):
        path = make_image(w=640, h=480)
        try:
            ok, size = analyze_resolution(path)
            assert ok is True
            assert size == (640, 480)
        finally:
            os.unlink(path)

    def test_too_small(self):
        path = make_tiny_image()
        try:
            ok, size = analyze_resolution(path)
            assert ok is False
        finally:
            os.unlink(path)

    def test_missing_file(self):
        ok, size = analyze_resolution("/nonexistent.jpg")
        assert ok is False


class TestRunModeration:
    def test_no_photos(self):
        result = run_moderation([])
        assert result["approved"] is False
        assert result["score"] == 0
        assert result["high_risk"] is True

    def test_wrong_count_one_photo(self):
        path = make_image()
        try:
            result = run_moderation([path])
            # No count bonus (5 pts missed), but score may have blur/res pts
            assert result["score"] < 80
            any_count_reason = any("фото" in r.lower() for r in result["reasons"])
            assert any_count_reason
        finally:
            os.unlink(path)

    def test_two_sharp_photos_no_location(self):
        p1 = make_image(noise=True)
        p2 = make_image(noise=True)
        try:
            result = run_moderation([p1, p2])
            assert isinstance(result["score"], int)
            assert 0 <= result["score"] <= 100
            assert "approved" in result
            assert "high_risk" in result
            assert "details" in result
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_score_includes_blur_and_resolution(self):
        p1 = make_image(noise=True, w=640, h=480)
        p2 = make_image(noise=True, w=640, h=480)
        try:
            result = run_moderation([p1, p2])
            # blur (10 pts) + resolution (5 pts) + count (5 pts) = 20 pts minimum
            assert result["details"]["blur"]["pts"] == 10
            assert result["details"]["resolution"]["pts"] == 5
            assert result["details"]["photo_count"]["ok"] is True
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_blurry_photos_score_lower(self):
        sharp1 = make_image(noise=True)
        sharp2 = make_image(noise=True)
        blur1 = make_image(noise=False)
        blur2 = make_image(noise=False)
        try:
            sharp_result = run_moderation([sharp1, sharp2])
            blur_result = run_moderation([blur1, blur2])
            assert sharp_result["score"] > blur_result["score"]
        finally:
            for p in [sharp1, sharp2, blur1, blur2]:
                os.unlink(p)

    def test_score_thresholds(self):
        # Score < 50 → high_risk
        # Score >= 80 → approved
        p1 = make_image()
        p2 = make_image()
        try:
            result = run_moderation([p1, p2])
            if result["score"] < 50:
                assert result["high_risk"] is True
                assert result["approved"] is False
            elif result["score"] >= 80:
                assert result["approved"] is True
                assert result["high_risk"] is False
            else:
                assert result["approved"] is False
                assert result["high_risk"] is False
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_return_structure(self):
        p1 = make_image()
        p2 = make_image()
        try:
            result = run_moderation([p1, p2])
            assert "approved" in result
            assert "score" in result
            assert "confidence_percent" in result
            assert "reasons" in result
            assert "details" in result
            assert "high_risk" in result
            assert isinstance(result["reasons"], list)
            assert isinstance(result["score"], int)
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_with_mocked_fresh_exif_and_gps(self):
        """Score should be high when EXIF timestamp is fresh and GPS matches."""
        moscow_lat, moscow_lon = 55.7558, 37.6173

        fresh_exif = {
            "datetime": datetime.now() - timedelta(minutes=20),
            "lat": moscow_lat,
            "lon": moscow_lon,
        }

        p1 = make_image(noise=True, w=640, h=480)
        p2 = make_image(noise=True, w=640, h=480)
        try:
            with patch("bot.utils.ai_moderation.extract_exif", return_value=fresh_exif):
                with patch("bot.utils.ai_moderation.detect_faces",
                           return_value={"found": True, "count": 5, "confidence": 0.95}):
                    result = run_moderation(
                        [p1, p2],
                        lat=moscow_lat,
                        lon=moscow_lon,
                    )
            # EXIF time(25) + GPS(20) + face(15) + audience(5) + blur(10) + res(5) + count(5) = 85
            assert result["score"] >= 80
            assert result["approved"] is True
            assert result["high_risk"] is False
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_with_mocked_stale_exif(self):
        """Score should be lower when EXIF timestamp is old."""
        stale_exif = {
            "datetime": datetime.now() - timedelta(hours=5),
            "lat": None,
            "lon": None,
        }

        p1 = make_image(noise=True)
        p2 = make_image(noise=True)
        try:
            with patch("bot.utils.ai_moderation.extract_exif", return_value=stale_exif):
                result = run_moderation([p1, p2])
            # No EXIF time pts (0) + No GPS pts (0)
            assert result["details"]["exif_timestamp"]["pts"] == 0
            assert result["score"] < 50  # at most blur+res+count = 20
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_with_mocked_gps_mismatch(self):
        """GPS mismatch reduces score by 20 pts."""
        moscow_lat, moscow_lon = 55.7558, 37.6173
        # Photo taken far away (Vladivostok)
        mismatched_exif = {
            "datetime": datetime.now() - timedelta(minutes=10),
            "lat": 43.1155,
            "lon": 131.8855,
        }

        p1 = make_image(noise=True)
        p2 = make_image(noise=True)
        try:
            with patch("bot.utils.ai_moderation.extract_exif", return_value=mismatched_exif):
                result = run_moderation([p1, p2], lat=moscow_lat, lon=moscow_lon)
            assert result["details"]["exif_gps"]["pts"] == 0
            assert any("GPS" in r or "км" in r or "м от" in r for r in result["reasons"])
        finally:
            os.unlink(p1)
            os.unlink(p2)
