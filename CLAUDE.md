# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Frontend dev server (hot reload, proxies API to :8000)
cd frontend && npm run dev

# Seed demo data (10 volunteers, 8 events, points, achievements)
python demo_data.py

# Run the application (FastAPI + built frontend at http://localhost:8000)
python bot/main.py

# One-command setup + run
chmod +x setup.sh && ./setup.sh

# Docker build
docker build -t volunteer-plus .
docker run -p 8000:8000 -e BOT_TOKEN=... -e ADMIN_PASSWORD=... volunteer-plus
```

### Environment variables (`.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOT_TOKEN` | — | Telegram bot token from @BotFather |
| `ADMIN_PASSWORD` | `admin123` | Coordinator password for bot + web login |
| `SECRET_KEY` | `hackathon-secret-key` | JWT signing key |
| `DB_PATH` | `./data/volunteer.db` | SQLite file path (set `/data/volunteer.db` in prod) |
| `DEMO_MODE` | `true` | Enables demo data endpoints |
| `WEBAPP_URL` | — | Public URL sent by bot for dashboard link |

---

## Key architectural note: `bot/main.py` current state

`bot/main.py` currently **only starts FastAPI/uvicorn** — it does not launch the Telegram bot dispatcher. The aiogram handlers in `bot/handlers/` are implemented but not wired into the running process. To re-enable the Telegram bot, connect the aiogram `Dispatcher` and `Bot` instances inside `main.py` alongside uvicorn.

---

# Волонтёр+ (VolunteerPlus)

**Продукт:** Волонтёр+ — платформа верификации волонтёрских мероприятий и координации команд.
**Целевая аудитория:** подростки 14–17 (волонтёры-амбассадоры), координаторы, родители.
**Стек:** Python 3.11+, aiogram 3.x, FastAPI, SQLite, React + Vite + Tailwind CSS, recharts.

---

## 1. PROJECT BRIEF

### Task 4. Offline Event Verification Bot

Context: Teenagers should become knowledge ambassadors — conducting lectures for younger classes, participating in city festivals. We need to verify they actually did it.

Goal: Build a bot or app that lets a teenager confirm they held an offline event.

Verification mechanics:
- Geolocation: mark the event location on a map (school, library)
- Photo report: upload 2-3 photos from the event (must NOT be downloaded from the internet)
- Organizer code: unique QR code from a coordinator/curator, scanned at the end of the lecture

Photo verification logic:
- Check EXIF metadata (timestamp, GPS coords must be recent and match geolocation)
- Require a selfie in front of the audience as one of the photos
- Optionally: use neural network / face detection to confirm live photo

Points: after successful verification — award points to the motivation system

---

### Task 5. Coordinator Dashboard

Context: Dozens of volunteers across different cities. Coordinator needs a "headquarters" to see the full picture. Excel is impossible. Need an automated tool.

Required features:
1. Volunteer registry: team list, contacts, status (active/inactive)
2. Task completion stats: how many lectures/workshops each volunteer conducted
3. Meeting calendar: scheduled vs completed events, attendance tracking
4. Ratings and achievements: who leads by activity, special achievements (youngest audience, largest crowd), visualization as charts or "podium"
5. UX requirement: coordinator opens it and sees everything within 1 minute

---

### Submission format requirements:
1. **Product name:** Волонтёр+
2. **Target audience:** teenager 14-17 (volunteer), coordinator, parent
3. **User flow:** step-by-step described in Section 5
4. **Prototype/screenshots:** demo mode with seeded data (see Section 6)
5. **Technologies:** Python, aiogram 3, FastAPI, SQLite, React, Vite, Tailwind CSS, recharts, OpenCV, Pillow, qrcode

---

## 2. ARCHITECTURE

### File structure

```
beeline/
├── CLAUDE.md                   # This file — project spec and rules
├── .env                        # Environment variables (BOT_TOKEN, ADMIN_PASSWORD)
├── .env.example                # Template for .env
├── .gitignore
├── requirements.txt            # Python dependencies
├── setup.sh                    # One-command setup + run
├── demo_data.py                # Seeds 10 volunteers, 8 events, points, achievements
│
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Entry point: starts aiogram bot + FastAPI + uvicorn
│   ├── config.py               # Reads .env, defines Settings
│   ├── database.py             # SQLite init, schema, helper queries
│   ├── strings.py              # ALL Russian UI strings (single source of truth)
│   │
│   ├── handlers/
│   │   ├── __init__.py         # Registers all routers
│   │   ├── start.py            # /start, role selection, registration
│   │   ├── volunteer.py        # Event submission FSM (location → photos → QR)
│   │   └── coordinator.py      # Admin menu, team, stats, calendar, QR generation
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── exif.py             # EXIF extraction (timestamp, GPS) via Pillow
│   │   ├── geo.py              # Haversine distance, geo validation (500m threshold)
│   │   ├── face.py             # Face detection via OpenCV Haar cascade
│   │   ├── qr.py               # QR generation (qrcode lib) + QR reading (OpenCV)
│   │   └── ai_moderation.py    # AI-based photo moderation (ai_score, ai_reasons)
│   │
│   └── api/
│       ├── __init__.py
│       ├── app.py              # FastAPI app factory, CORS, SPA static file serving
│       └── routes/
│           ├── __init__.py
│           ├── auth.py         # POST /api/auth/login (coordinator JWT), POST /api/auth/register
│           ├── volunteers.py   # GET /api/volunteers, GET /api/volunteers/:id
│           ├── events.py       # GET/POST/PATCH /api/events
│           ├── stats.py        # GET /api/stats, /api/leaderboard, /api/achievements
│           ├── verification.py # POST /api/events/:id/verify (photo+GPS verification)
│           └── applications.py # GET/POST /api/events/:id/applications (event sign-ups)
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       ├── api.js              # Axios/fetch wrapper for API calls
│       ├── pages/
│       │   ├── Login.jsx       # Coordinator login
│       │   ├── Dashboard.jsx   # Overview: key metrics, recent activity
│       │   ├── Team.jsx        # Volunteer registry with status
│       │   ├── Calendar.jsx    # Event calendar (planned + completed)
│       │   └── Ratings.jsx     # Leaderboard, podium, achievements
│       └── components/
│           ├── Sidebar.jsx     # Navigation sidebar
│           ├── StatsCard.jsx   # Metric card with icon
│           ├── Leaderboard.jsx # Top-N table with podium
│           └── EventCard.jsx   # Single event display
```

### Database schema

The actual schema is defined in `bot/database.py:init_db()`. Key differences from the original spec:

- `volunteers` has additional columns: `email TEXT UNIQUE`, `password_hash TEXT` (for web login)
- `events` has additional columns: `created_by INTEGER REFERENCES volunteers(id)`, `moderation_note TEXT`; status enum expanded to include `'pending'` and `'rejected'`
- New tables added beyond the original spec:

```
event_verifications  — per-event photo/GPS submissions with AI scoring fields
                       (ai_score, ai_approved, ai_reasons, coordinator_decision)
event_applications   — volunteer sign-ups for events (pending/approved/rejected)
event_reviews        — post-event ratings (1–5 stars + comment) from volunteers
```

```sql
-- Core tables (abbreviated — see bot/database.py for full DDL)
volunteers(id, telegram_id, username, full_name, city, phone, email, password_hash,
           role, status, points, created_at)
events(id, title, description, location_name, location_lat, location_lon,
       scheduled_date, status, qr_code, coordinator_id, created_by,
       moderation_note, attendance_count, created_at)
event_verifications(id, event_id, volunteer_id, photo_paths, volunteer_comment,
                    location_lat, location_lon, ai_score, ai_approved, ai_reasons,
                    coordinator_decision, coordinator_comment, created_at)
submissions(id, volunteer_id, event_id, location_lat, location_lon, photo_count,
            selfie_verified, geo_verified, exif_verified, qr_verified, qr_code,
            points_awarded, status, rejection_reason, created_at)
event_applications(id, event_id, volunteer_id, full_name, email, phone, status, created_at)
event_reviews(id, event_id, volunteer_id, rating, comment, created_at)
achievements(id, volunteer_id, badge_type, title, description, created_at)
points_history(id, volunteer_id, amount, reason, submission_id, created_at)
```

### Data flow: volunteer submission → points

```
1. Volunteer sends /start → bot creates record in volunteers table
2. Volunteer taps "Подать отчёт" → FSM enters waiting_location state
3. Volunteer shares location → bot stores lat/lon in FSM context
4. Volunteer uploads 2–3 photos → for each photo:
   a. Download to /tmp
   b. Extract EXIF (Pillow): check datetime within 2 hours
   c. Extract GPS from EXIF: check distance ≤ 500m from submitted location
   d. Run face detection (OpenCV Haar): at least 1 photo must have a face
   e. DELETE photo from disk immediately
5. Volunteer sends QR code (text or photo) → bot decodes and validates against events.qr_code
6. All checks pass → bot:
   a. Creates submission record (status='verified')
   b. Awards 50 points (+ bonuses)
   c. Updates volunteers.points
   d. Inserts into points_history
   e. Checks for achievements, inserts if earned
   f. Sends confirmation with total score
7. Any check fails → bot explains which check failed, submission not created
```

### How Task 4 and Task 5 connect

- **Shared DB:** both the Telegram bot and FastAPI read/write the same SQLite file
- **Shared entity:** `volunteers` table is the central entity
- **Events link:** coordinator creates events (with QR) via Task 5; volunteer validates against those events via Task 4
- **Points flow:** Task 4 awards points → Task 5 displays them in leaderboard/stats
- **Real-time:** FastAPI dashboard reads fresh data on every request; no caching needed for hackathon

---

## 3. DEVELOPMENT RULES

These are **imperatives**, not suggestions:

1. **ALWAYS** start a new feature by writing the DB schema change first
2. **ALWAYS** handle Telegram API errors with try/except — never let the bot crash silently
3. **NEVER** store photos permanently — check metadata and discard immediately
4. **ALWAYS** validate QR codes server-side — never trust client input
5. **ALWAYS** check EXIF: timestamp must be within last 2 hours, GPS must match submitted geolocation within 500 meters
6. **ALWAYS** require one selfie-style photo (face detected) among the 2–3 uploads
7. **ALWAYS** respond to every Telegram message — no silent failures
8. **NEVER** leave broken code — use `# TODO:` stubs if needed but code **must** run
9. After implementing any handler — test it with `/start` before moving on
10. Keep **all** text strings in `bot/strings.py` (single source of truth for localization)
11. After any DB schema change — update the schema section in this CLAUDE.md
12. **ALWAYS** use parameterized queries — never format SQL strings manually
13. **NEVER** commit `.env` or `data/` directory to git

---

## 4. HOW TO RUN

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Telegram bot token from @BotFather

### Get a Telegram bot token

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Choose a name (e.g., "Волонтёр+ Бот")
4. Choose a username (e.g., `volunteer_plus_bot`)
5. Copy the token, paste into `.env` as `BOT_TOKEN`

### Quick start (one command)

```bash
chmod +x setup.sh && ./setup.sh
```

### Manual start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Create .env from template
cp .env.example .env
# Edit .env: set BOT_TOKEN and ADMIN_PASSWORD

# 3. Build frontend
cd frontend && npm install && npm run build && cd ..

# 4. Seed demo data
python demo_data.py

# 5. Run the bot + dashboard
python bot/main.py
```

### After running

- **Telegram bot:** open the bot in Telegram by its username
- **Web dashboard:** open http://localhost:8000 in browser
- **API docs:** open http://localhost:8000/docs (Swagger UI)

### Seed demo data

```bash
python demo_data.py
```

Creates: 10 volunteers, 5 past events (verified), 3 upcoming events, points distributed, leaderboard populated.

### 5-minute demo for judges

1. Run `python demo_data.py` to seed data
2. Run `python bot/main.py`
3. Open http://localhost:8000 — show dashboard (team, stats, leaderboard, calendar)
4. Open Telegram bot:
   - Show volunteer flow: /start → submit event → location → photos → QR
   - Show coordinator flow: /start → coordinator → generate QR → view team
5. Refresh dashboard — show new data appeared

---

## 5. USER FLOWS

### Volunteer flow (Task 4)

1. `/start` → bot sends welcome message, asks: "Выберите роль" → [Волонтёр] [Координатор]
2. Volunteer taps [Волонтёр]
3. If new user → bot asks for name, city → creates profile
4. Bot shows volunteer menu: [Подать отчёт] [Моя статистика] [Мои достижения]
5. Volunteer taps [Подать отчёт]
6. Bot: "Отправьте геолокацию места проведения" → volunteer shares live location
7. Bot: "Отправьте 2–3 фотографии (одна — селфи)" → volunteer uploads one by one
8. For each photo, bot checks:
   - EXIF timestamp: within last 2 hours? → ✅ / ❌ with explanation
   - EXIF GPS: within 500m of submitted location? → ✅ / ❌ with explanation
   - Face detection: is this a selfie? → tracks if at least 1 photo has a face
9. After 2–3 photos received, if no selfie detected → ❌ "Селфи не обнаружено"
10. Bot: "Отсканируйте QR-код организатора" → volunteer sends text or photo
11. Bot validates QR against DB → ✅ / ❌
12. **All checks pass →** bot awards 50 points, shows confirmation: "🎉 +50 баллов! Всего: 250"
13. **Any check fails →** bot explains what failed, offers to retry

### Coordinator flow (Task 5)

1. `/start` → coordinator taps [Координатор]
2. Bot: "Введите пароль координатора" → coordinator enters password
3. Password correct → bot shows coordinator menu:
   [👥 Команда] [📊 Статистика] [📅 Календарь] [🏆 Рейтинг] [🔲 Создать QR] [🌐 Дашборд]
4. **[Команда]** → list of volunteers with status, tap one → see their submissions and points
5. **[Статистика]** → total events this week/month, completion rate, top 3 performers
6. **[Календарь]** → upcoming events marked 🔵, completed marked ✅, tap to see details
7. **[Рейтинг]** → podium top-3, full leaderboard sorted by points
8. **[Создать QR]** → bot asks: event title → date → location → generates QR image, sends to coordinator
9. **[Дашборд]** → bot sends link to http://localhost:8000

---

## 6. DEMO DATA SCRIPT

Run: `python demo_data.py`

### What it creates:

**10 volunteers:**
| # | Name | City | Points | Status |
|---|------|------|--------|--------|
| 1 | Алиса Иванова | Москва | 350 | active |
| 2 | Борис Петров | Санкт-Петербург | 280 | active |
| 3 | Виктория Сидорова | Казань | 220 | active |
| 4 | Григорий Козлов | Новосибирск | 190 | active |
| 5 | Дарья Новикова | Екатеринбург | 150 | active |
| 6 | Евгений Морозов | Москва | 120 | active |
| 7 | Жанна Волкова | Санкт-Петербург | 80 | active |
| 8 | Захар Лебедев | Казань | 50 | inactive |
| 9 | Ирина Соколова | Новосибирск | 30 | active |
| 10 | Кирилл Попов | Екатеринбург | 10 | active |

**5 past events (completed, with submissions):**
1. "Лекция по программированию" — Москва, 2026-03-20, attendance: 25
2. "Мастер-класс по робототехнике" — СПб, 2026-03-18, attendance: 15
3. "Воркшоп по дизайну" — Казань, 2026-03-15, attendance: 30
4. "Лекция по экологии" — Новосибирск, 2026-03-12, attendance: 20
5. "Фестиваль науки" — Екатеринбург, 2026-03-10, attendance: 50

**3 upcoming events (planned):**
1. "Хакатон для школьников" — Москва, 2026-04-05
2. "Лекция по ИИ" — СПб, 2026-04-10
3. "Мастер-класс по 3D-печати" — Казань, 2026-04-15

**Achievements distributed:**
- Алиса: "Первая лекция", "Марафонец" (5+ events)
- Борис: "Первая лекция", "Звезда сцены" (largest crowd)
- Виктория: "Первая лекция"

**Points history:** each volunteer has entries matching their total points.
