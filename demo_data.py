"""
Seed script for Волонтёр+ demo data.
Creates 10 volunteers, 8 events (5 completed + 3 planned),
submissions, points history, and achievements.

Run: python demo_data.py
"""

import os
import sqlite3
import uuid

DB_PATH = os.getenv("DB_PATH", "data/volunteer.db")

SCHEMA = """
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

VOLUNTEERS = [
    (100001, "alisa_iv", "Алиса Иванова", "Москва", "+79001111111", "volunteer", "active", 350),
    (100002, "boris_p", "Борис Петров", "Санкт-Петербург", "+79002222222", "volunteer", "active", 280),
    (100003, "vika_s", "Виктория Сидорова", "Казань", "+79003333333", "volunteer", "active", 220),
    (100004, "grigory_k", "Григорий Козлов", "Новосибирск", "+79004444444", "volunteer", "active", 190),
    (100005, "darya_n", "Дарья Новикова", "Екатеринбург", "+79005555555", "volunteer", "active", 150),
    (100006, "evgeny_m", "Евгений Морозов", "Москва", "+79006666666", "volunteer", "active", 120),
    (100007, "zhanna_v", "Жанна Волкова", "Санкт-Петербург", "+79007777777", "volunteer", "active", 80),
    (100008, "zahar_l", "Захар Лебедев", "Казань", "+79008888888", "volunteer", "inactive", 50),
    (100009, "irina_s", "Ирина Соколова", "Новосибирск", "+79009999999", "volunteer", "active", 30),
    (100010, "kirill_p", "Кирилл Попов", "Екатеринбург", "+79001010101", "volunteer", "active", 10),
]

# Coordinator
COORDINATOR = (200001, "coordinator_main", "Мария Координаторова", "Москва", "+79000000001", "coordinator", "active", 0)

COMPLETED_EVENTS = [
    ("Лекция по программированию", "Введение в Python для школьников", "Школа №42, Москва",
     55.7558, 37.6173, "2026-03-20", "completed", 25),
    ("Мастер-класс по робототехнике", "Основы Arduino", "Библиотека им. Ленина, СПб",
     59.9343, 30.3351, "2026-03-18", "completed", 15),
    ("Воркшоп по дизайну", "Figma для начинающих", "Технопарк, Казань",
     55.7887, 49.1221, "2026-03-15", "completed", 30),
    ("Лекция по экологии", "Раздельный сбор мусора", "ДК Молодёжи, Новосибирск",
     55.0084, 82.9357, "2026-03-12", "completed", 20),
    ("Фестиваль науки", "Физика в повседневной жизни", "Уральский ТЦ, Екатеринбург",
     56.8389, 60.6057, "2026-03-10", "completed", 50),
]

PLANNED_EVENTS = [
    ("Хакатон для школьников", "24-часовой хакатон по разработке приложений", "Технопарк, Москва",
     55.7558, 37.6173, "2026-04-05", "planned", 0),
    ("Лекция по ИИ", "Как работает ChatGPT", "IT-парк, Санкт-Петербург",
     59.9343, 30.3351, "2026-04-10", "planned", 0),
    ("Мастер-класс по 3D-печати", "Создаём первую модель", "FabLab, Казань",
     55.7887, 49.1221, "2026-04-15", "planned", 0),
]

# Submissions: (volunteer_idx, event_idx, points)
# volunteer_idx is 0-based index into VOLUNTEERS
# event_idx is 0-based index into COMPLETED_EVENTS
SUBMISSIONS = [
    # Алиса — 7 submissions across events (350 points)
    (0, 0, 50), (0, 1, 50), (0, 2, 50), (0, 3, 50), (0, 4, 50), (0, 0, 50), (0, 1, 50),
    # Борис — 5 submissions (280 points)
    (1, 0, 56), (1, 1, 56), (1, 2, 56), (1, 3, 56), (1, 4, 56),
    # Виктория — 4 submissions (220 points)
    (2, 2, 55), (2, 3, 55), (2, 4, 55), (2, 0, 55),
    # Григорий — 3 submissions (190 points, some with bonuses)
    (3, 3, 65), (3, 4, 65), (3, 0, 60),
    # Дарья — 3 submissions (150 points)
    (4, 4, 50), (4, 0, 50), (4, 1, 50),
    # Евгений — 2 submissions (120 points)
    (5, 0, 60), (5, 1, 60),
    # Жанна — 1 submission (80 points)
    (6, 1, 80),
    # Захар — 1 submission (50 points)
    (7, 2, 50),
    # Ирина — 1 submission (30 points)
    (8, 3, 30),
    # Кирилл — 0 verified, 1 rejected (10 points from partial)
    (9, 4, 10),
]

ACHIEVEMENTS = [
    # Алиса
    (0, "first_event", "Первая лекция", "Провела первое мероприятие"),
    (0, "marathon", "Марафонец", "5+ мероприятий проведено"),
    (0, "ambassador", "Амбассадор", "Самый активный волонтёр месяца"),
    # Борис
    (1, "first_event", "Первая лекция", "Провёл первое мероприятие"),
    (1, "star", "Звезда сцены", "Самая большая аудитория — 50 человек"),
    # Виктория
    (2, "first_event", "Первая лекция", "Провела первое мероприятие"),
    (2, "multicity", "Мультигород", "Мероприятия в разных городах"),
    # Григорий
    (3, "first_event", "Первая лекция", "Провёл первое мероприятие"),
    # Дарья
    (4, "first_event", "Первая лекция", "Провела первое мероприятие"),
    # Евгений
    (5, "first_event", "Первая лекция", "Провёл первое мероприятие"),
]


def main():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

    # Remove old DB for clean seed
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Удалена старая БД: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    # Insert coordinator
    conn.execute(
        "INSERT INTO volunteers (telegram_id, username, full_name, city, phone, role, status, points) VALUES (?,?,?,?,?,?,?,?)",
        COORDINATOR,
    )
    coordinator_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert volunteers
    volunteer_ids = []
    for v in VOLUNTEERS:
        conn.execute(
            "INSERT INTO volunteers (telegram_id, username, full_name, city, phone, role, status, points) VALUES (?,?,?,?,?,?,?,?)",
            v,
        )
        vid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        volunteer_ids.append(vid)
    print(f"Создано {len(volunteer_ids)} волонтёров + 1 координатор")

    # Insert completed events
    event_ids = []
    for title, desc, loc, lat, lon, date, status, attendance in COMPLETED_EVENTS:
        qr = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            "INSERT INTO events (title, description, location_name, location_lat, location_lon, scheduled_date, status, qr_code, coordinator_id, attendance_count) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (title, desc, loc, lat, lon, date, status, qr, coordinator_id, attendance),
        )
        eid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        event_ids.append(eid)
    print(f"Создано {len(event_ids)} завершённых мероприятий")

    # Insert planned events
    planned_ids = []
    for title, desc, loc, lat, lon, date, status, attendance in PLANNED_EVENTS:
        qr = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            "INSERT INTO events (title, description, location_name, location_lat, location_lon, scheduled_date, status, qr_code, coordinator_id, attendance_count) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (title, desc, loc, lat, lon, date, status, qr, coordinator_id, attendance),
        )
        eid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        planned_ids.append(eid)
    print(f"Создано {len(planned_ids)} запланированных мероприятий")

    # Insert submissions and points history
    submission_count = 0
    for vol_idx, evt_idx, points in SUBMISSIONS:
        vid = volunteer_ids[vol_idx]
        eid = event_ids[evt_idx]
        evt_qr = conn.execute("SELECT qr_code FROM events WHERE id = ?", (eid,)).fetchone()[0]
        evt = conn.execute("SELECT location_lat, location_lon FROM events WHERE id = ?", (eid,)).fetchone()

        conn.execute(
            """INSERT INTO submissions
               (volunteer_id, event_id, location_lat, location_lon, photo_count,
                selfie_verified, geo_verified, exif_verified, qr_verified,
                qr_code, points_awarded, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (vid, eid, evt[0], evt[1], 3, 1, 1, 1, 1, evt_qr, points, "verified"),
        )
        sub_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO points_history (volunteer_id, amount, reason, submission_id) VALUES (?,?,?,?)",
            (vid, points, f"Верификация мероприятия #{eid}", sub_id),
        )
        submission_count += 1

    print(f"Создано {submission_count} отчётов (submissions)")

    # Insert achievements
    for vol_idx, badge, title, desc in ACHIEVEMENTS:
        vid = volunteer_ids[vol_idx]
        conn.execute(
            "INSERT INTO achievements (volunteer_id, badge_type, title, description) VALUES (?,?,?,?)",
            (vid, badge, title, desc),
        )
    print(f"Создано {len(ACHIEVEMENTS)} достижений")

    conn.commit()
    conn.close()

    print(f"\nБД создана: {DB_PATH}")
    print("Демо-данные загружены успешно!")
    print("\nДля запуска бота: python bot/main.py")


if __name__ == "__main__":
    main()
