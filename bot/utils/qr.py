import io
import logging
import random
import string

import cv2
import qrcode

logger = logging.getLogger(__name__)


def generate_qr_image(data: str) -> bytes:
    """Generate a QR code PNG image as bytes."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def read_qr_from_image(image_path: str) -> str | None:
    """Read QR code from an image file. Returns decoded text or None."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning("Could not read image for QR: %s", image_path)
            return None

        detector = cv2.QRCodeDetector()
        data, vertices, _ = detector.detectAndDecode(img)

        if data:
            logger.info("QR decoded: %s", data)
            return data
        return None
    except Exception as e:
        logger.error("QR reading error: %s", e)
        return None


def generate_event_code() -> str:
    """Generate a unique event code like EVT-XXXXXX."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"EVT-{suffix}"
