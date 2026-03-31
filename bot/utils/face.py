import logging

import cv2

logger = logging.getLogger(__name__)

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def _haar_detect_faces(image_path: str) -> dict:
    """Haar Cascade face detection. Returns dict with found/count/confidence."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning("Could not read image: %s", image_path)
            return {"found": False, "count": 0, "confidence": 0.0}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )

        count = len(faces)
        found = count > 0
        logger.info("Haar face detection on %s: found=%s (count=%d)", image_path, found, count)
        return {"found": found, "count": count, "confidence": 0.9 if found else 0.0}
    except Exception as e:
        logger.error("Haar face detection error: %s", e)
        return {"found": False, "count": 0, "confidence": 0.0}


def detect_faces(image_path: str) -> dict:
    """Detect faces. Tries MediaPipe first, falls back to Haar Cascade.

    Returns {"found": bool, "count": int, "confidence": float}
    """
    try:
        import mediapipe as mp

        mp_face = mp.solutions.face_detection.FaceDetection(
            min_detection_confidence=0.5,
            model_selection=0,  # 0=short range (≤2m, selfie), 1=full range
        )
        img = cv2.imread(image_path)
        if img is None:
            return _haar_detect_faces(image_path)

        results = mp_face.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        mp_face.close()

        if not results.detections:
            return {"found": False, "count": 0, "confidence": 0.0}

        count = len(results.detections)
        confidence = max(d.score[0] for d in results.detections)
        logger.info("MediaPipe face detection on %s: found=True (count=%d)", image_path, count)
        return {"found": True, "count": count, "confidence": float(confidence)}

    except ImportError:
        logger.debug("MediaPipe not available, falling back to Haar Cascade")
        return _haar_detect_faces(image_path)
    except Exception as e:
        logger.error("MediaPipe face detection error: %s, falling back to Haar", e)
        return _haar_detect_faces(image_path)


def detect_face(image_path: str) -> bool:
    """Backward-compatible wrapper. Returns True if at least one face found."""
    return detect_faces(image_path)["found"]
