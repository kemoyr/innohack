import hashlib
import os
import uuid
from datetime import datetime, timedelta

import aiosqlite

from bot.config import settings

DB_PATH = settings.DB_PATH


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT DEFAULT '',
                full_name TEXT NOT NULL,
                city TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT UNIQUE,
                password_hash TEXT DEFAULT '',
                role TEXT DEFAULT 'volunteer' CHECK(role IN ('volunteer', 'coordinator')),
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
                points INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                location_name TEXT DEFAULT '',
                location_lat REAL,
                location_lon REAL,
                scheduled_date TEXT,
                status TEXT DEFAULT 'planned' CHECK(status IN ('pending', 'planned', 'completed', 'cancelled', 'rejected')),
                qr_code TEXT UNIQUE,
                coordinator_id INTEGER REFERENCES volunteers(id),
                created_by INTEGER REFERENCES volunteers(id),
                moderation_note TEXT DEFAULT '',
                attendance_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS event_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL REFERENCES events(id),
                volunteer_id INTEGER NOT NULL REFERENCES volunteers(id),
                photo_paths TEXT DEFAULT '[]',
                volunteer_comment TEXT DEFAULT '',
                location_lat REAL,
                location_lon REAL,
                ai_score REAL DEFAULT 0,
                ai_approved INTEGER DEFAULT 0,
                ai_reasons TEXT DEFAULT '[]',
                coordinator_decision TEXT DEFAULT '' CHECK(coordinator_decision IN ('', 'approved', 'rejected')),
                coordinator_comment TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_id INTEGER NOT NULL REFERENCES volunteers(id),
                event_id INTEGER REFERENCES events(id),
                location_lat REAL,
                location_lon REAL,
                photo_count INTEGER DEFAULT 0,
                selfie_verified INTEGER DEFAULT 0,
                geo_verified INTEGER DEFAULT 0,
                exif_verified INTEGER DEFAULT 0,
                qr_verified INTEGER DEFAULT 0,
                qr_code TEXT,
                points_awarded INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'verified', 'rejected')),
                rejection_reason TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_id INTEGER NOT NULL REFERENCES volunteers(id),
                badge_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS points_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_id INTEGER NOT NULL REFERENCES volunteers(id),
                amount INTEGER NOT NULL,
                reason TEXT DEFAULT '',
                submission_id INTEGER REFERENCES submissions(id),
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS event_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL REFERENCES events(id),
                volunteer_id INTEGER NOT NULL REFERENCES volunteers(id),
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT DEFAULT '',
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(event_id, volunteer_id)
            );

            CREATE TABLE IF NOT EXISTS event_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL REFERENCES events(id),
                volunteer_id INTEGER NOT NULL REFERENCES volunteers(id),
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(event_id, volunteer_id)
            );

            CREATE INDEX IF NOT EXISTS idx_event_applications_event ON event_applications(event_id);
            CREATE INDEX IF NOT EXISTS idx_event_applications_volunteer ON event_applications(volunteer_id);
            CREATE INDEX IF NOT EXISTS idx_event_reviews_event ON event_reviews(event_id);
            CREATE INDEX IF NOT EXISTS idx_event_reviews_volunteer ON event_reviews(volunteer_id);

            CREATE INDEX IF NOT EXISTS idx_volunteers_telegram_id ON volunteers(telegram_id);
            CREATE INDEX IF NOT EXISTS idx_volunteers_email ON volunteers(email);
            CREATE INDEX IF NOT EXISTS idx_submissions_volunteer_id ON submissions(volunteer_id);
            CREATE INDEX IF NOT EXISTS idx_submissions_event_id ON submissions(event_id);
            CREATE INDEX IF NOT EXISTS idx_events_qr_code ON events(qr_code);
            CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
            CREATE INDEX IF NOT EXISTS idx_events_created_by ON events(created_by);
            CREATE INDEX IF NOT EXISTS idx_event_verifications_event_id ON event_verifications(event_id);
            CREATE INDEX IF NOT EXISTS idx_points_history_volunteer_id ON points_history(volunteer_id);
            """
        )
        # Migration: add columns if missing (for existing DBs)
        for col, default in [
            ("email", "NULL"), ("password_hash", "''"),
            ("created_by", "NULL"), ("moderation_note", "''"),
        ]:
            try:
                table = "volunteers" if col in ("email", "password_hash") else "events"
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT {default}")
            except Exception:
                pass
        try:
            await db.execute(
                "ALTER TABLE event_verifications ADD COLUMN volunteer_comment TEXT DEFAULT ''"
            )
        except Exception:
            pass
        # Auto-seed demo data if DB is empty
        cursor = await db.execute("SELECT COUNT(*) FROM volunteers")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await _seed_demo_data(db)

        await db.commit()


def _hash_pw(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + dk.hex()


async def _seed_demo_data(db):
    """Insert demo volunteers, events, submissions, achievements."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Database is empty — seeding demo data...")

    pw = _hash_pw("demo123")

    now = datetime.now()

    def _rel(days_offset: int) -> str:
        return (now + timedelta(days=days_offset)).strftime("%Y-%m-%d")

    await db.execute(
        """INSERT INTO volunteers (telegram_id, username, full_name, city, phone, email, password_hash, role, status, points)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (200001, "coordinator_main", "Мария Координаторова", "Москва", "+79000000001",
         "coordinator@example.com", pw, "coordinator", "active", 0),
    )

    volunteers = [
        (100001, "alisa_iv", "Алиса Иванова", "Москва", "+79001111111", "alisa@example.com", "volunteer", "active", 350),
        (100002, "boris_p", "Борис Петров", "Санкт-Петербург", "+79002222222", "boris@example.com", "volunteer", "active", 280),
        (100003, "vika_s", "Виктория Сидорова", "Казань", "+79003333333", "vika@example.com", "volunteer", "active", 220),
        (100004, "grigory_k", "Григорий Козлов", "Новосибирск", "+79004444444", "grigory@example.com", "volunteer", "active", 190),
        (100005, "darya_n", "Дарья Новикова", "Екатеринбург", "+79005555555", "darya@example.com", "volunteer", "active", 150),
        (100006, "evgeny_m", "Евгений Морозов", "Москва", "+79006666666", "evgeny@example.com", "volunteer", "active", 120),
        (100007, "zhanna_v", "Жанна Волкова", "Санкт-Петербург", "+79007777777", "zhanna@example.com", "volunteer", "active", 80),
        (100008, "zahar_l", "Захар Лебедев", "Казань", "+79008888888", "zahar@example.com", "volunteer", "inactive", 50),
        (100009, "irina_s", "Ирина Соколова", "Новосибирск", "+79009999999", "irina@example.com", "volunteer", "active", 30),
        (100010, "kirill_p", "Кирилл Попов", "Екатеринбург", "+79001010101", "kirill@example.com", "volunteer", "active", 10),
    ]
    for tg_id, username, name, city, phone, email, role, status, points in volunteers:
        await db.execute(
            """INSERT INTO volunteers (telegram_id, username, full_name, city, phone, email, password_hash, role, status, points)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (tg_id, username, name, city, phone, email, pw, role, status, points),
        )

    completed_events = [
        ("Лекция по программированию", "Введение в Python для школьников", "Школа №42, Москва", 55.7558, 37.6173, _rel(0), "completed", 25),
        ("Мастер-класс по робототехнике", "Основы Arduino", "Библиотека им. Ленина, СПб", 59.9343, 30.3351, _rel(-2), "completed", 15),
        ("Воркшоп по дизайну", "Figma для начинающих", "Технопарк, Казань", 55.7887, 49.1221, _rel(-5), "completed", 30),
        ("Лекция по экологии", "Раздельный сбор мусора", "ДК Молодёжи, Новосибирск", 55.0084, 82.9357, _rel(-8), "completed", 20),
        ("Фестиваль науки", "Физика в повседневной жизни", "Уральский ТЦ, Екатеринбург", 56.8389, 60.6057, _rel(-11), "completed", 50),
    ]
    event_ids = []
    for title, desc, loc, lat, lon, date, status, attendance in completed_events:
        qr = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        await db.execute(
            """INSERT INTO events (title, description, location_name, location_lat, location_lon,
                                   scheduled_date, status, qr_code, coordinator_id, attendance_count)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (title, desc, loc, lat, lon, date, status, qr, 1, attendance),
        )
        cursor = await db.execute("SELECT last_insert_rowid()")
        event_ids.append((await cursor.fetchone())[0])

    # Planned events
    planned_events = [
        ("Хакатон для школьников", "24-часовой хакатон по разработке приложений", "Технопарк, Москва", 55.7558, 37.6173, _rel(5), "planned", 0),
        ("Лекция по ИИ", "Как работает ChatGPT", "IT-парк, Санкт-Петербург", 59.9343, 30.3351, _rel(10), "planned", 0),
        ("Мастер-класс по 3D-печати", "Создаём первую модель", "FabLab, Казань", 55.7887, 49.1221, _rel(16), "planned", 0),
    ]
    for title, desc, loc, lat, lon, date, status, attendance in planned_events:
        qr = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        await db.execute(
            """INSERT INTO events (title, description, location_name, location_lat, location_lon,
                                   scheduled_date, status, qr_code, coordinator_id, attendance_count)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (title, desc, loc, lat, lon, date, status, qr, 1, attendance),
        )

    # Submissions + points (volunteer IDs start at 2)
    submissions = [
        (0,0,50),(0,1,50),(0,2,50),(0,3,50),(0,4,50),(0,0,50),(0,1,50),
        (1,0,56),(1,1,56),(1,2,56),(1,3,56),(1,4,56),
        (2,2,55),(2,3,55),(2,4,55),(2,0,55),
        (3,3,65),(3,4,65),(3,0,60),
        (4,4,50),(4,0,50),(4,1,50),
        (5,0,60),(5,1,60),
        (6,1,80),
        (7,2,50),
        (8,3,30),
        (9,4,10),
    ]
    for vol_idx, evt_idx, points in submissions:
        vid = vol_idx + 2  # volunteers start at id=2
        eid = event_ids[evt_idx]
        cursor = await db.execute("SELECT qr_code, location_lat, location_lon FROM events WHERE id = ?", (eid,))
        evt = await cursor.fetchone()
        await db.execute(
            """INSERT INTO submissions
               (volunteer_id, event_id, location_lat, location_lon, photo_count,
                selfie_verified, geo_verified, exif_verified, qr_verified,
                qr_code, points_awarded, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (vid, eid, evt[1], evt[2], 3, 1, 1, 1, 1, evt[0], points, "verified"),
        )
        cursor = await db.execute("SELECT last_insert_rowid()")
        sub_id = (await cursor.fetchone())[0]
        await db.execute(
            "INSERT INTO points_history (volunteer_id, amount, reason, submission_id) VALUES (?,?,?,?)",
            (vid, points, f"Верификация мероприятия #{eid}", sub_id),
        )

    # Achievements
    achievements = [
        (0, "first_event", "Первая лекция", "Провела первое мероприятие"),
        (0, "marathon", "Марафонец", "5+ мероприятий проведено"),
        (0, "ambassador", "Амбассадор", "Самый активный волонтёр месяца"),
        (1, "first_event", "Первая лекция", "Провёл первое мероприятие"),
        (1, "star", "Звезда сцены", "Провёл мероприятие с аншлагом"),
        (2, "first_event", "Первая лекция", "Провела первое мероприятие"),
        (2, "multicity", "Мультигород", "Мероприятия в разных городах"),
        (3, "first_event", "Первая лекция", "Провёл первое мероприятие"),
        (4, "first_event", "Первая лекция", "Провела первое мероприятие"),
        (5, "first_event", "Первая лекция", "Провёл первое мероприятие"),
    ]
    for vol_idx, badge, title, desc in achievements:
        vid = vol_idx + 2
        await db.execute(
            "INSERT INTO achievements (volunteer_id, badge_type, title, description) VALUES (?,?,?,?)",
            (vid, badge, title, desc),
        )

    logger.info("Demo data seeded: 1 coordinator + 10 volunteers, 8 events, 28 submissions, 10 achievements")
    logger.info("Coordinator: coordinator@example.com / demo123")
    logger.info("Volunteer: alisa@example.com / demo123")


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)

async def get_volunteer(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM volunteers WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def get_volunteer_by_id(volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM volunteers WHERE id = ?", (volunteer_id,)
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def get_volunteer_by_email(email: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM volunteers WHERE email = ?", (email,)
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def create_volunteer(
    telegram_id=None,
    username: str = "",
    full_name: str = "",
    city: str = "",
    phone: str = "",
    role: str = "volunteer",
    email: str = None,
    password_hash: str = "",
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO volunteers (telegram_id, username, full_name, city, phone, role, email, password_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, full_name, city, phone, role, email, password_hash),
        )
        await db.commit()
        return cursor.lastrowid


async def update_volunteer_points(volunteer_id: int, points_delta: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE volunteers SET points = points + ? WHERE id = ?",
            (points_delta, volunteer_id),
        )
        await db.commit()


async def get_all_volunteers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM volunteers ORDER BY points DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_submission_counts_by_volunteer() -> dict[int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT volunteer_id, COUNT(*) FROM submissions GROUP BY volunteer_id"
        )
        rows = await cursor.fetchall()
        return {int(r[0]): int(r[1]) for r in rows if r[0] is not None}


async def get_volunteer_submissions(volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM submissions WHERE volunteer_id = ? ORDER BY created_at DESC",
            (volunteer_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def create_event(
    title: str,
    description: str = "",
    location_name: str = "",
    lat=None,
    lon=None,
    scheduled_date: str = "",
    qr_code: str = "",
    coordinator_id=None,
    created_by=None,
    status: str = "planned",
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO events (title, description, location_name, location_lat, location_lon,
                                   scheduled_date, qr_code, coordinator_id, created_by, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, location_name, lat, lon, scheduled_date,
             qr_code or None, coordinator_id, created_by, status),
        )
        await db.commit()
        return cursor.lastrowid


async def get_event_by_id(event_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def get_event_by_qr(qr_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE qr_code = ?", (qr_code,)
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def get_all_events():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM events ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_public_events():
    """Events visible to public (not pending/rejected)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE status IN ('planned', 'completed', 'cancelled') ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_pending_events():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE status = 'pending' ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_events_by_creator(volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE created_by = ? ORDER BY created_at DESC",
            (volunteer_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_planned_events():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE status = 'planned' ORDER BY scheduled_date ASC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_completed_events():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE status = 'completed' ORDER BY scheduled_date DESC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_event_status(event_id: int, status: str, attendance_count: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE events SET status = ?, attendance_count = ? WHERE id = ?",
            (status, attendance_count, event_id),
        )
        await db.commit()


async def moderate_event(event_id: int, status: str, note: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE events SET status = ?, moderation_note = ? WHERE id = ?",
            (status, note, event_id),
        )
        await db.commit()

async def create_event_verification(
    event_id: int, volunteer_id: int, photo_paths: str = "[]",
    volunteer_comment: str = "",
    lat=None, lon=None, ai_score: float = 0, ai_approved: int = 0, ai_reasons: str = "[]",
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO event_verifications
               (event_id, volunteer_id, photo_paths, volunteer_comment, location_lat, location_lon,
                ai_score, ai_approved, ai_reasons)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, volunteer_id, photo_paths, volunteer_comment or "", lat, lon,
             ai_score, ai_approved, ai_reasons),
        )
        await db.commit()
        return cursor.lastrowid


async def delete_verifications_for_event(event_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM event_verifications WHERE event_id = ?", (event_id,))
        await db.commit()


async def get_event_verification(event_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM event_verifications WHERE event_id = ? ORDER BY created_at DESC LIMIT 1",
            (event_id,),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def get_pending_verifications():
    """Get all verifications for pending events needing coordinator review."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ev.*, e.title as event_title, e.status as event_status,
                      e.scheduled_date, e.location_name, v.full_name as volunteer_name
               FROM event_verifications ev
               JOIN events e ON ev.event_id = e.id
               JOIN volunteers v ON ev.volunteer_id = v.id
               WHERE e.status = 'pending' AND ev.coordinator_decision = ''
               ORDER BY ev.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_verifications():
    """Full moderation history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ev.*, e.title as event_title, e.status as event_status,
                      e.scheduled_date, e.location_name, v.full_name as volunteer_name
               FROM event_verifications ev
               JOIN events e ON ev.event_id = e.id
               JOIN volunteers v ON ev.volunteer_id = v.id
               ORDER BY ev.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_verification_decision(verification_id: int, decision: str, comment: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE event_verifications SET coordinator_decision = ?, coordinator_comment = ? WHERE id = ?",
            (decision, comment, verification_id),
        )
        await db.commit()

async def create_submission(
    volunteer_id: int, event_id=None, lat=None, lon=None,
    photo_count: int = 0, selfie_verified: int = 0,
    geo_verified: int = 0, exif_verified: int = 0,
    qr_verified: int = 0, qr_code: str = "",
    points_awarded: int = 0, status: str = "pending",
    rejection_reason: str = "",
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO submissions
               (volunteer_id, event_id, location_lat, location_lon, photo_count,
                selfie_verified, geo_verified, exif_verified, qr_verified,
                qr_code, points_awarded, status, rejection_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (volunteer_id, event_id, lat, lon, photo_count,
             selfie_verified, geo_verified, exif_verified, qr_verified,
             qr_code, points_awarded, status, rejection_reason),
        )
        await db.commit()
        return cursor.lastrowid


# ── Leaderboard & Points ─────────


async def get_leaderboard(limit: int | None = None):
    """All volunteers with role volunteer, ordered by points (new registrations included)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if limit is not None:
            cursor = await db.execute(
                """SELECT * FROM volunteers WHERE role = 'volunteer'
                   ORDER BY points DESC, id ASC LIMIT ?""",
                (limit,),
            )
        else:
            cursor = await db.execute(
                """SELECT * FROM volunteers WHERE role = 'volunteer'
                   ORDER BY points DESC, id ASC"""
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def add_points(volunteer_id: int, amount: int, reason: str = "", submission_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO points_history (volunteer_id, amount, reason, submission_id)
               VALUES (?, ?, ?, ?)""",
            (volunteer_id, amount, reason, submission_id),
        )
        await db.execute(
            "UPDATE volunteers SET points = points + ? WHERE id = ?",
            (amount, volunteer_id),
        )
        await db.commit()


async def get_volunteer_points_history(volunteer_id: int, limit: int = 200):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM points_history WHERE volunteer_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (volunteer_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ── Achievements ──────────────────


async def add_achievement(volunteer_id: int, badge_type: str, title: str, description: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO achievements (volunteer_id, badge_type, title, description)
               VALUES (?, ?, ?, ?)""",
            (volunteer_id, badge_type, title, description),
        )
        await db.commit()
        return cursor.lastrowid


async def get_achievements(volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM achievements WHERE volunteer_id = ? ORDER BY created_at DESC",
            (volunteer_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM events WHERE status != 'pending'")
        total_events = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM events WHERE status = 'completed'"
        )
        completed_events = (await cursor.fetchone())["cnt"]

        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        month_start = now.strftime("%Y-%m-01")

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM events WHERE scheduled_date >= ? AND status != 'pending'",
            (week_start,),
        )
        this_week_events = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM events WHERE scheduled_date >= ? AND status != 'pending'",
            (month_start,),
        )
        this_month_events = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM volunteers WHERE role = 'volunteer'")
        total_volunteers = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM volunteers WHERE status = 'active' AND role = 'volunteer'"
        )
        active_volunteers = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM events WHERE status = 'pending'")
        pending_events = (await cursor.fetchone())["cnt"]

    return {
        "total_events": total_events,
        "completed_events": completed_events,
        "this_week_events": this_week_events,
        "this_month_events": this_month_events,
        "total_volunteers": total_volunteers,
        "active_volunteers": active_volunteers,
        "pending_events": pending_events,
    }

async def get_nominations():
    """Automatically computed nominations from real event/submission data
    (replaces static/demographic badges like "youngest listener", which would
    require data we don't collect)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """SELECT id, title, location_name, scheduled_date, attendance_count
               FROM events
               WHERE status = 'completed' AND attendance_count > 0
               ORDER BY attendance_count DESC
               LIMIT 1"""
        )
        top_event = await cursor.fetchone()
        biggest_audience = None
        if top_event:
            cursor = await db.execute(
                """SELECT v.id, v.full_name
                   FROM submissions s
                   JOIN volunteers v ON v.id = s.volunteer_id
                   WHERE s.event_id = ? AND s.status = 'verified'
                   ORDER BY s.points_awarded DESC
                   LIMIT 1""",
                (top_event["id"],),
            )
            volunteer = await cursor.fetchone()
            biggest_audience = {
                "event_id": top_event["id"],
                "event_title": top_event["title"],
                "location_name": top_event["location_name"],
                "scheduled_date": top_event["scheduled_date"],
                "attendance_count": top_event["attendance_count"],
                "volunteer_id": volunteer["id"] if volunteer else None,
                "volunteer_name": volunteer["full_name"] if volunteer else None,
            }

        cursor = await db.execute(
            """SELECT v.id, v.full_name, v.city, COUNT(*) as event_count
               FROM submissions s
               JOIN volunteers v ON v.id = s.volunteer_id
               WHERE s.status = 'verified'
               GROUP BY v.id
               ORDER BY event_count DESC
               LIMIT 1"""
        )
        row = await cursor.fetchone()
        most_active = dict(row) if row else None

        cursor = await db.execute(
            """SELECT v.id, v.full_name, v.city, COUNT(DISTINCT e.location_name) as city_count
               FROM submissions s
               JOIN volunteers v ON v.id = s.volunteer_id
               JOIN events e ON e.id = s.event_id
               WHERE s.status = 'verified'
               GROUP BY v.id
               HAVING city_count > 1
               ORDER BY city_count DESC
               LIMIT 1"""
        )
        row = await cursor.fetchone()
        multi_city = dict(row) if row else None

    return {
        "biggest_audience": biggest_audience,
        "most_active": most_active,
        "multi_city": multi_city,
    }


async def mark_qr_used(qr_code: str, volunteer_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id FROM submissions WHERE qr_code = ? AND volunteer_id = ?",
            (qr_code, volunteer_id),
        )
        row = await cursor.fetchone()
        return row is not None

async def toggle_volunteer_status(volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT status FROM volunteers WHERE id = ?", (volunteer_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        new_status = "inactive" if row["status"] == "active" else "active"
        await db.execute(
            "UPDATE volunteers SET status = ? WHERE id = ?",
            (new_status, volunteer_id),
        )
        await db.commit()
        return new_status

async def get_recent_submissions(limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT s.*, v.full_name as volunteer_name, e.title as event_title
            FROM submissions s
            LEFT JOIN volunteers v ON s.volunteer_id = v.id
            LEFT JOIN events e ON s.event_id = e.id
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def create_application(event_id: int, volunteer_id: int, full_name: str, email: str, phone: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO event_applications (event_id, volunteer_id, full_name, email, phone)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, volunteer_id, full_name, email, phone),
        )
        await db.commit()
        return cursor.lastrowid


async def get_application(event_id: int, volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM event_applications WHERE event_id = ? AND volunteer_id = ?",
            (event_id, volunteer_id),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def get_event_applications(event_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ea.*, v.full_name as volunteer_name, v.city
               FROM event_applications ea
               JOIN volunteers v ON ea.volunteer_id = v.id
               WHERE ea.event_id = ?
               ORDER BY ea.created_at DESC""",
            (event_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_volunteer_applications(volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ea.*, e.title as event_title, e.scheduled_date, e.location_name, e.status as event_status
               FROM event_applications ea
               JOIN events e ON ea.event_id = e.id
               WHERE ea.volunteer_id = ?
               ORDER BY ea.created_at DESC""",
            (volunteer_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_event_application_count(event_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM event_applications WHERE event_id = ?",
            (event_id,),
        )
        row = await cursor.fetchone()
        return row[0]


# ── Event Reviews ──────────────


async def get_volunteer_event_review(event_id: int, volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM event_reviews WHERE event_id = ? AND volunteer_id = ?",
            (event_id, volunteer_id),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def create_review(event_id: int, volunteer_id: int, rating: int, comment: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO event_reviews (event_id, volunteer_id, rating, comment)
               VALUES (?, ?, ?, ?)""",
            (event_id, volunteer_id, rating, comment),
        )
        await db.commit()
        return cursor.lastrowid


async def get_event_reviews(event_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT er.*, v.full_name as volunteer_name
               FROM event_reviews er
               JOIN volunteers v ON er.volunteer_id = v.id
               WHERE er.event_id = ?
               ORDER BY er.created_at DESC""",
            (event_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_volunteer_reviews(volunteer_id: int):
    """Reviews written BY this volunteer."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT er.*, e.title as event_title, e.scheduled_date
               FROM event_reviews er
               JOIN events e ON er.event_id = e.id
               WHERE er.volunteer_id = ?
               ORDER BY er.created_at DESC""",
            (volunteer_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_event_avg_rating(event_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM event_reviews WHERE event_id = ?",
            (event_id,),
        )
        row = await cursor.fetchone()
        return {"avg_rating": round(row[0], 1) if row[0] else 0, "count": row[1]}


async def get_recent_achievements(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT a.*, v.full_name as volunteer_name
            FROM achievements a
            LEFT JOIN volunteers v ON a.volunteer_id = v.id
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
