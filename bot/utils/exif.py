import logging
from datetime import datetime

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = logging.getLogger(__name__)


def _get_exif_data(image_path: str) -> dict:
    try:
        img = Image.open(image_path)
        exif_raw = img._getexif()
        if not exif_raw:
            return {}
        exif = {}
        for tag_id, value in exif_raw.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value
        return exif
    except Exception as e:
        logger.warning("Failed to read EXIF: %s", e)
        return {}


def _get_gps_info(exif: dict) -> dict:
    gps_info = exif.get("GPSInfo")
    if not gps_info:
        return {}
    gps = {}
    for key, val in gps_info.items():
        decoded = GPSTAGS.get(key, key)
        gps[decoded] = val
    return gps


def _dms_to_decimal(dms, ref: str) -> float:
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        decimal = degrees + minutes / 60.0 + seconds / 3600.0
        if ref in ("S", "W"):
            decimal = -decimal
        return decimal
    except Exception as e:
        logger.warning("Failed to convert DMS to decimal: %s", e)
        return None


def extract_exif(image_path: str) -> dict:
    result = {"datetime": None, "lat": None, "lon": None}

    exif = _get_exif_data(image_path)
    if not exif:
        return result

    dt_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
    if dt_str:
        try:
            result["datetime"] = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        except (ValueError, TypeError) as e:
            logger.warning("Failed to parse EXIF datetime '%s': %s", dt_str, e)

    gps = _get_gps_info(exif)
    if gps:
        lat_dms = gps.get("GPSLatitude")
        lat_ref = gps.get("GPSLatitudeRef", "N")
        lon_dms = gps.get("GPSLongitude")
        lon_ref = gps.get("GPSLongitudeRef", "E")

        if lat_dms and lon_dms:
            result["lat"] = _dms_to_decimal(lat_dms, lat_ref)
            result["lon"] = _dms_to_decimal(lon_dms, lon_ref)

    return result


def is_recent(dt: datetime, max_hours: int = 2) -> bool:
    if dt is None:
        return False
    now = datetime.now()
    diff = abs((now - dt).total_seconds())
    return diff <= max_hours * 3600
