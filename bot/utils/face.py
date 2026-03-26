import logging

import cv2

logger = logging.getLogger(__name__)

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def detect_face(image_path: str) -> bool:
    """Detect if at least one face is present in the image."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning("Could not read image: %s", image_path)
            return False

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )

        found = len(faces) > 0
        logger.info("Face detection on %s: found=%s (count=%d)", image_path, found, len(faces))
        return found
    except Exception as e:
        logger.error("Face detection error: %s", e)
        return False
