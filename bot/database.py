import os
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
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                full_name TEXT NOT NULL,
                city TEXT DEFAULT '',
                phone TEXT DEFAULT '',
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
                status TEXT DEFAULT 'planned' CHECK(status IN ('planned', 'completed', 'cancelled')),
                qr_code TEXT UNIQUE,
                coordinator_id INTEGER REFERENCES volunteers(id),
                attendance_count INTEGER DEFAULT 0,
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

            CREATE INDEX IF NOT EXISTS idx_volunteers_telegram_id ON volunteers(telegram_id);
            CREATE INDEX IF NOT EXISTS idx_submissions_volunteer_id ON submissions(volunteer_id);
            CREATE INDEX IF NOT EXISTS idx_submissions_event_id ON submissions(event_id);
            CREATE INDEX IF NOT EXISTS idx_events_qr_code ON events(qr_code);
            CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
            CREATE INDEX IF NOT EXISTS idx_points_history_volunteer_id ON points_history(volunteer_id);
            """
        )
        await db.commit()


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


# ── Volunteers ────────────────────


async def get_volunteer(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM volunteers WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def create_volunteer(
    telegram_id: int,
    username: str,
    full_name: str,
    city: str = "",
    phone: str = "",
    role: str = "volunteer",
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO volunteers (telegram_id, username, full_name, city, phone, role)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, full_name, city, phone, role),
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


async def get_volunteer_submissions(volunteer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM submissions WHERE volunteer_id = ? ORDER BY created_at DESC",
            (volunteer_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ── Events ────────────────────────


async def create_event(
    title: str,
    description: str = "",
    location_name: str = "",
    lat=None,
    lon=None,
    scheduled_date: str = "",
    qr_code: str = "",
    coordinator_id=None,
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO events (title, description, location_name, location_lat, location_lon,
                                   scheduled_date, qr_code, coordinator_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, location_name, lat, lon, scheduled_date, qr_code, coordinator_id),
        )
        await db.commit()
        return cursor.lastrowid


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


# ── Submissions ───────────────────


async def create_submission(
    volunteer_id: int,
    event_id,
    lat,
    lon,
    photo_count: int = 0,
    selfie_verified: int = 0,
    geo_verified: int = 0,
    exif_verified: int = 0,
    qr_verified: int = 0,
    qr_code: str = "",
    points_awarded: int = 0,
    status: str = "pending",
    rejection_reason: str = "",
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO submissions
               (volunteer_id, event_id, location_lat, location_lon, photo_count,
                selfie_verified, geo_verified, exif_verified, qr_verified,
                qr_code, points_awarded, status, rejection_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                volunteer_id, event_id, lat, lon, photo_count,
                selfie_verified, geo_verified, exif_verified, qr_verified,
                qr_code, points_awarded, status, rejection_reason,
            ),
        )
        await db.commit()
        return cursor.lastrowid


# ── Leaderboard & Points ─────────


async def get_leaderboard(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM volunteers WHERE role = 'volunteer' ORDER BY points DESC LIMIT ?",
            (limit,),
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


# ── Stats ─────────────────────────


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM events")
        total_events = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM events WHERE status = 'completed'"
        )
        completed_events = (await cursor.fetchone())["cnt"]

        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        month_start = now.strftime("%Y-%m-01")

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM events WHERE scheduled_date >= ?",
            (week_start,),
        )
        this_week_events = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM events WHERE scheduled_date >= ?",
            (month_start,),
        )
        this_month_events = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM volunteers")
        total_volunteers = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM volunteers WHERE status = 'active'"
        )
        active_volunteers = (await cursor.fetchone())["cnt"]

    return {
        "total_events": total_events,
        "completed_events": completed_events,
        "this_week_events": this_week_events,
        "this_month_events": this_month_events,
        "total_volunteers": total_volunteers,
        "active_volunteers": active_volunteers,
    }


# ── QR usage check ───────────────


async def mark_qr_used(qr_code: str, volunteer_id: int) -> bool:
    """Return True if QR was already used by this volunteer (i.e. duplicate)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id FROM submissions WHERE qr_code = ? AND volunteer_id = ?",
            (qr_code, volunteer_id),
        )
        row = await cursor.fetchone()
        return row is not None


# ── Toggle volunteer status ──────


async def toggle_volunteer_status(volunteer_id: int):
    """Toggle volunteer status between active and inactive. Returns new status."""
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


# ── Recent activity helpers ──────


async def get_recent_submissions(limit: int = 20):
    """Get recent submissions with volunteer and event info."""
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


async def get_recent_achievements(limit: int = 10):
    """Get recent achievements with volunteer info."""
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
