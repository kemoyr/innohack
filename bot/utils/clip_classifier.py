"""CLIP-based event photo classifier (inference only).

Loads a fine-tuned classification head on top of frozen openai/clip-vit-base-patch16.
Weights file: bot/models/clip_event_classifier.pt  (download from Kaggle notebook).

Head architecture (must match notebooks/train_clip_classifier.ipynb):
    LayerNorm(512) → Dropout(0.2) → Linear(512→128) → GELU
    → Dropout(0.1) → Linear(128→2)

Preprocessing at inference uses the same albumentations val pipeline as during training:
    Resize(224, 224) → Normalize(CLIP_MEAN, CLIP_STD) → ToTensorV2
This ensures no train/inference preprocessing mismatch.
"""
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_MODELS_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = _MODELS_DIR / "clip_event_classifier.pt"
CLIP_MODEL_ID = "openai/clip-vit-base-patch16"

# Нормализация CLIP (должна совпадать с тренировочным пайплайном)
_CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD = (0.26862954, 0.26130258, 0.27577711)
_CLIP_IMAGE_SIZE = 224

# Ленивые синглтоны
_clip_model = None
_head = None
_transforms = None
_available: bool | None = None  # None = ещё не проверяли


def _check_available() -> bool:
    global _available
    if _available is not None:
        return _available

    if not MODEL_PATH.exists():
        logger.info(
            "CLIP weights not found at %s — Block 4 will be skipped", MODEL_PATH
        )
        _available = False
        return False

    missing = []
    for pkg in ("torch", "transformers", "albumentations"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        logger.info("Missing packages for CLIP: %s — Block 4 skipped", missing)
        _available = False
        return False

    _available = True
    return True


def _build_transforms():
    """Создаёт albumentations val pipeline — идентичен val_transforms из ноутбука."""
    import albumentations as A
    from albumentations.pytorch import ToTensorV2

    return A.Compose([
        A.Resize(_CLIP_IMAGE_SIZE, _CLIP_IMAGE_SIZE),
        A.Normalize(mean=_CLIP_MEAN, std=_CLIP_STD, max_pixel_value=255.0),
        ToTensorV2(),
    ])


def _build_head(embed_dim: int = 512):
    """Строит classification head — архитектура должна совпадать с ноутбуком."""
    import torch.nn as nn

    return nn.Sequential(
        nn.LayerNorm(embed_dim),
        nn.Dropout(p=0.2),
        nn.Linear(embed_dim, 128),
        nn.GELU(),
        nn.Dropout(p=0.1),
        nn.Linear(128, 2),
    )


def _load() -> None:
    """Загружает CLIP encoder и head в память (один раз при первом вызове)."""
    global _clip_model, _head, _transforms

    if _clip_model is not None:
        return

    import torch
    from transformers import CLIPModel

    logger.info("Loading CLIP model %s...", CLIP_MODEL_ID)
    _clip_model = CLIPModel.from_pretrained(CLIP_MODEL_ID)
    for param in _clip_model.parameters():
        param.requires_grad = False
    _clip_model.eval()

    embed_dim = _clip_model.config.projection_dim  # 512 для vit-base-patch16

    _head = _build_head(embed_dim)
    _head.load_state_dict(
        torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    )
    _head.eval()

    _transforms = _build_transforms()

    logger.info(
        "CLIP classifier loaded (embed_dim=%d, weights=%s)", embed_dim, MODEL_PATH
    )


def classify_event_photo(image_path: str) -> dict:
    """Предсказывает вероятность того, что фото сделано на мероприятии.

    Returns:
        {
            "available":          bool    – False если модель не загружена
            "event_probability":  float   – 0.0..1.0
            "is_event":           bool    – True если >= 0.5
        }

    Если веса отсутствуют или пакеты не установлены — возвращает нейтральный
    результат {"available": False, "event_probability": 0.5, "is_event": True}
    чтобы не штрафовать score при отсутствии модели.
    """
    _NEUTRAL = {"available": False, "event_probability": 0.5, "is_event": True}

    if not _check_available():
        return _NEUTRAL

    try:
        import torch
        from PIL import Image

        _load()

        # Preprocessing — идентично val_transforms из ноутбука
        pil_img = Image.open(image_path).convert("RGB")
        img_np = np.array(pil_img, dtype=np.uint8)
        augmented = _transforms(image=img_np)
        pixel_values = augmented["image"].unsqueeze(0)  # [1, 3, 224, 224]

        with torch.no_grad():
            features = _clip_model.get_image_features(pixel_values=pixel_values)
            logits = _head(features)
            probs = torch.softmax(logits, dim=1)[0]

        p_event = float(probs[1])
        return {
            "available": True,
            "event_probability": round(p_event, 4),
            "is_event": p_event >= 0.5,
        }

    except Exception as e:
        logger.error("CLIP inference error on %s: %s", image_path, e)
        return _NEUTRAL
