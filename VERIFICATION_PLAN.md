# Верификация фотографий мероприятий — план реализации

## Проблема

`bot/utils/ai_moderation.py` → `run_moderation()` возвращает `random.randint(30, 100)`.
Алгоритмические проверки (blur, resolution, face) реализованы, но не складываются в единый скор.
`exif.py` и `geo.py` существуют, но не вызываются из `run_moderation()`.
ML-части нет вообще.

---

## Архитектура итогового pipeline

```
Входные данные:
  photo_paths: list[str]     временные файлы, удаляются после анализа
  lat, lon: float            геолокация от волонтёра
  submission_time: datetime  момент подачи
  title: str

для каждого фото:
  ┌─────────────────────────────────────────────┐
  │ Блок 1: EXIF                                │
  │   extract_exif(path)                        │
  │   · timestamp ≤ 2 ч от submission_time      │
  │   · GPS из EXIF vs submitted ≤ 500 м        │
  └─────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────┐
  │ Блок 2: качество фото                       │
  │   · blur: Laplacian variance                │
  │   · resolution: минимум 320×240             │
  └─────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────┐
  │ Блок 3: MediaPipe face detection            │
  │   · есть ли лицо (селфи-проверка)          │
  │   · сколько лиц (сигнал аудитории)          │
  └─────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────┐
  │ Блок 4: CLIP-классификатор (fine-tuned)     │
  │   · P(фото с мероприятия) → 0..1           │
  │   · модель обучена на WIDER датасете        │
  └─────────────────────────────────────────────┘
         │
  aggregate_score() → 0–100 pts
  ├── ≥ 80  → approved=True  (авто-одобрение)
  ├── 50–79 → coordinator queue
  └── < 50  → coordinator queue + флаг high_risk
```

---

## Балльная система (0–100)

| # | Блок | Проверка | Макс. баллов |
|---|------|---------|-------------|
| 1 | EXIF | timestamp свежий (≤ 2 ч) | 25 |
| 2 | EXIF | GPS совпадает с геолокацией (≤ 500 м) | 20 |
| 3 | Faces | хотя бы одно лицо на фото | 15 |
| 4 | CLIP | P(event) ≥ 0.5 | 15 |
| 5 | Blur | Laplacian variance > 80 на всех фото | 10 |
| 6 | Resolution | w ≥ 320, h ≥ 240 | 5 |
| 7 | Count | загружено 2–3 фото | 5 |
| — | Бонус | ≥ 3 лиц (аудитория) | +5 |
| | | **Итого** | **100** |

Частичные баллы (блоки 4, 5, 6) — если порог не достигнут, но значение разумное,
начисляется половина баллов.

---

## Блок 1: EXIF (интеграция готового кода)

`exif.py` и `geo.py` уже написаны и работают, просто не вызываются из `run_moderation()`.

```python
from bot.utils.exif import extract_exif, is_recent
from bot.utils.geo import haversine

exif = extract_exif(path)

# Timestamp
if exif["datetime"] and is_recent(exif["datetime"], max_hours=2):
    score += 25
elif exif["datetime"]:
    reasons.append(f"Фото #{i+1}: снято более 2 часов назад")
else:
    reasons.append(f"Фото #{i+1}: нет EXIF timestamp")

# GPS vs submitted location
if exif["lat"] and exif["lon"] and submitted_lat and submitted_lon:
    dist = haversine(exif["lat"], exif["lon"], submitted_lat, submitted_lon)
    if dist <= 500:
        score += 20
    else:
        reasons.append(f"Фото #{i+1}: GPS в EXIF = {dist:.0f} м от указанной точки")
```

---

## Блок 2: Качество фото (уже реализовано, оставить)

`analyze_blur()` и `analyze_resolution()` в `ai_moderation.py` работают корректно.
Просто включить их в итоговый скор вместо игнорирования.

---

## Блок 3: MediaPipe (замена Haar Cascade)

**Почему MediaPipe вместо Haar Cascade:** Haar Cascade даёт много false-negative
при профильных фото, масках, плохом освещении. MediaPipe работает офлайн,
~30 мс/фото на CPU, детектирует под углом, возвращает число лиц и confidence.

**Файл:** `bot/utils/face.py` — переписать, оставить Haar как fallback.

```python
def detect_faces(image_path: str) -> dict:
    """Returns {"found": bool, "count": int, "confidence": float}"""
    try:
        import mediapipe as mp
        mp_face = mp.solutions.face_detection.FaceDetection(
            min_detection_confidence=0.5,
            model_selection=0,   # 0=short range (≤2м, селфи), 1=full range
        )
        img = cv2.imread(image_path)
        results = mp_face.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.detections:
            return {"found": False, "count": 0, "confidence": 0.0}
        return {
            "found": True,
            "count": len(results.detections),
            "confidence": max(d.score[0] for d in results.detections),
        }
    except ImportError:
        # fallback to Haar Cascade
        return _haar_detect_face(image_path)
```

Начисление баллов:
```python
face = detect_faces(path)
if face["found"]:
    score += 15
    if face["count"] >= 3:   # много людей — аудитория
        score += 5
```

---

## Блок 4: CLIP fine-tuned классификатор

### Почему fine-tune, а не zero-shot

Zero-shot CLIP сравнивает изображение с текстом через dot-product эмбеддингов.
Для специфической задачи «фото с мероприятия» он нестабилен: нет гарантий, что
наши текстовые описания соответствуют тому, как CLIP «видит» сцену.

Fine-tune решает это: замораживаем visual encoder CLIP, добавляем
`Linear(embed_dim, 2)` поверх и обучаем на реальных фото событий.
Text encoder при inference не используется вообще.

### Выбор модели

**`openai/clip-vit-base-patch16`** (не patch32):
- patch16 делит изображение на 196 токенов (14×14) против 49 у patch32
- Больше токенов → лучше детализация → выше точность на плотных сценах (аудитория)
- Размер модели: ~600 МБ, такой же как patch32
- Подходит для fine-tune на RTX 2060 Super (8 GB) при batch_size=16–24

### Датасет: составной из трёх источников

Единого датасета «фото с волонтёрского мероприятия» не существует.
Собираем из нескольких источников, каждый покрывает свой тип примеров.

#### Источник 1 — WIDER FACE (positives + часть negatives)

**Ссылка:** [`CUHK-CSE/wider_face`](https://hf.co/datasets/CUHK-CSE/wider_face)

32k изображений, каждое размечено по одной из **61 категории событий**.
Фото сделаны на реальных событиях *с людьми* в кадре.

| Класс | Категории из WIDER |
|-------|-------------------|
| `event` (1) | `Lecture`, `Meeting`, `Press_conference`, `Ceremony`, `Commencement`, `Pageant`, `Festival` |
| `not_event` (0) | `Basketball`, `Swimming`, `Tennis`, `Running`, `Soccer`, `Volleyball`, `Aerobics`, `Baseball` и остальные спортивные |

Примерный выход: ~5k positive, ~8k negative (спорт).

#### Источник 2 — Places365 (negatives: бытовые и природные сцены)

**Ссылка:** [`Andron00e/Places365-custom`](https://hf.co/datasets/Andron00e/Places365-custom)

1.8M фото, 365 сцен. Берём выборку по категориям, которые имитируют «не-мероприятие»:

| Тип | Категории Places365 |
|-----|---------------------|
| Бытовые интерьеры | `bedroom`, `bathroom`, `kitchen`, `living_room`, `corridor`, `closet` |
| Природа / улица | `forest`, `beach`, `mountain`, `field`, `street`, `parking_lot` |
| Общественные, но не лекция | `restaurant`, `bar`, `market`, `shopping_mall` |

Берём ~500 фото на категорию → ~8–10k negatives.
Places365 важен потому что это сцены **без людей или с людьми не на мероприятии** —
именно такие фото может прислать недобросовестный волонтёр.

#### Источник 3 — MIT Indoor Scenes (hard negatives)

**Ссылка:** [`keremberke/indoor-scene-classification`](https://hf.co/datasets/keremberke/indoor-scene-classification)

Используем как **хардкорный негатив**: берём категории `classroom` и `lecture_theatre`.
Это стоковые/архивные фото пустых аудиторий — визуально похожи на мероприятие,
но людей нет или сцена явно постановочная. Модель должна научиться их отклонять.

~500–800 hard negative примеров.

#### Итоговый баланс датасета

| Класс | Источник | Кол-во |
|-------|---------|-------|
| `event` (1) | WIDER FACE (лекции, митинги, церемонии) | ~5 000 |
| `not_event` (0) | WIDER FACE (спорт) | ~8 000 |
| `not_event` (0) | Places365 (бытовые + природа) | ~8 000 |
| `not_event` (0) | MIT Indoor Scenes hard negatives | ~700 |
| **Итого** | | **~22 000** |

Соотношение: 1:3.4 (event vs not_event) → компенсируем через `class_weight`.

### Kaggle-ноутбук: `notebooks/train_clip_classifier.ipynb`

Обучать на Kaggle (T4/P100), а не локально, по двум причинам:
1. Датасет весит ~1.5 ГБ — незачем хранить локально
2. На Kaggle данные загружаются прямо из HuggingFace без скачивания

```python
# ── 1. Зависимости ──────────────────────────────────
# !pip install transformers datasets torch torchvision

# ── 2. Загрузка датасета ─────────────────────────────
from datasets import load_dataset
ds = load_dataset("CUHK-CSE/wider_face")

# ── 3. Ремаппинг меток ───────────────────────────────
EVENT_CLASSES = {
    "Lecture", "Meeting", "Press_conference",
    "Ceremony", "Commencement", "Pageant", "Festival",
}

def remap(example):
    event_name = example["event_label"]   # строка, напр. "Lecture"
    example["is_event"] = 1 if event_name in EVENT_CLASSES else 0
    return example

ds = ds.map(remap)

# ── 4. Подготовка CLIP visual encoder ────────────────
from transformers import CLIPModel, CLIPProcessor
import torch
import torch.nn as nn

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

# Замораживаем всё, кроме classifier head
for param in model.parameters():
    param.requires_grad = False

classifier = nn.Linear(model.config.projection_dim, 2)   # 512 → 2
# (только classifier обучается)

# ── 5. DataLoader ─────────────────────────────────────
from torch.utils.data import DataLoader
from PIL import Image

def collate(batch):
    images = [item["image"].convert("RGB") for item in batch]
    labels = torch.tensor([item["is_event"] for item in batch])
    inputs = processor(images=images, return_tensors="pt", padding=True)
    return inputs, labels

train_ds = ds["train"].shuffle(seed=42)
loader = DataLoader(train_ds, batch_size=24, collate_fn=collate)

# ── 6. Обучение ──────────────────────────────────────
optimizer = torch.optim.AdamW(classifier.parameters(), lr=1e-4)
# class_weights чтобы компенсировать дисбаланс классов
loss_fn = nn.CrossEntropyLoss(weight=torch.tensor([1.0, 3.0]))  # event в 3× меньше

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device); classifier.to(device)

for epoch in range(5):
    for inputs, labels in loader:
        inputs = {k: v.to(device) for k, v in inputs.items()}
        labels = labels.to(device)

        image_features = model.get_image_features(**inputs)   # [B, 512]
        logits = classifier(image_features)
        loss = loss_fn(logits, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

# ── 7. Экспорт ───────────────────────────────────────
torch.save(classifier.state_dict(), "clip_event_classifier.pt")
# → скачать и положить как bot/models/clip_event_classifier.pt
```

### Inference в проекте: `bot/utils/clip_classifier.py`

```python
import torch
import torch.nn as nn
from transformers import CLIPModel, CLIPProcessor
from PIL import Image

_model = _processor = _classifier = None
MODEL_PATH = "bot/models/clip_event_classifier.pt"

def _load():
    global _model, _processor, _classifier
    if _model is None:
        _model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16")
        _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")
        for p in _model.parameters():
            p.requires_grad = False
        _classifier = nn.Linear(_model.config.projection_dim, 2)
        _classifier.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        _model.eval(); _classifier.eval()

def classify_event_photo(image_path: str) -> dict:
    """Returns {"event_probability": float, "is_event": bool}"""
    _load()
    image = Image.open(image_path).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = _model.get_image_features(**inputs)
        logits = _classifier(features)
        probs = torch.softmax(logits, dim=1)[0]
    p_event = float(probs[1])
    return {"event_probability": round(p_event, 3), "is_event": p_event >= 0.5}
```

Начисление баллов:
```python
clip = classify_event_photo(path)
if clip["event_probability"] >= 0.5:
    score += 15
elif clip["event_probability"] >= 0.3:
    score += 7     # частичный балл: сцена неоднозначна
else:
    reasons.append(f"Фото #{i+1}: CLIP не распознал мероприятие ({clip['event_probability']:.0%})")
```

---

## Изменения в `verification.py`

После замены `random` на реальный скор — включить авто-одобрение:

```python
result = run_moderation(...)

if result["approved"]:   # score >= 80
    await moderate_event(
        event_id, "planned",
        f"Авто-одобрено (AI score: {result['score']:.0f}/100)"
    )
    await update_verification_decision(ver_id, "approved", "auto")
# иначе — попадает в очередь координатора, как сейчас
```

---

## Зависимости

```
# добавить в requirements.txt
mediapipe>=0.10.0
transformers>=4.35.0
torch>=2.0.0
```

CLIP (~600 МБ) кешируется в `~/.cache/huggingface/hub/` при первом запуске.
`clip_event_classifier.pt` (~2 МБ) хранится в репозитории в `bot/models/`.

---

## Порядок реализации

```
Шаг 1  bot/utils/ai_moderation.py
       Убрать random. Реализовать балльную систему.
       Интегрировать EXIF (блок 1) и geo.

Шаг 2  bot/utils/face.py
       Заменить Haar Cascade на MediaPipe + fallback.

Шаг 3  notebooks/train_clip_classifier.ipynb
       Запустить на Kaggle, скачать clip_event_classifier.pt.

Шаг 4  bot/utils/clip_classifier.py
       Новый файл, inference CLIP + classifier head.

Шаг 5  bot/utils/ai_moderation.py
       Добавить вызов classify_event_photo() (блок 4).

Шаг 6  bot/api/routes/verification.py
       Авто-одобрение при score ≥ 80.
```

---

## Что НЕ реализуем

- **Zero-shot CLIP** — без fine-tune нестабилен на специфической задаче
- **MIT Indoor Scenes** — пустые комнаты, не подходит для детекции событий с людьми
- **Double JPEG compression detection** — слишком много false positive на телефонных фото
- **Reverse image search** — требует внешнего API-ключа, ненадёжен офлайн
- **Google Vision / Azure** — платные API, внешняя зависимость
