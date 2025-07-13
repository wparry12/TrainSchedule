import sqlite3
import json 

DB_FILE = "train_schedule.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        departure_time TEXT NOT NULL,
        cancelled BOOLEAN NOT NULL DEFAULT 0,
        party_train BOOLEAN NOT NULL DEFAULT 0,
        school_name TEXT DEFAULT ''
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carriages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        number TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        occupied BOOLEAN NOT NULL DEFAULT 0,
        group_size INTEGER NOT NULL DEFAULT 0,
        toddlers INTEGER NOT NULL DEFAULT 0,
        wheelchair BOOLEAN NOT NULL DEFAULT 0,
        group_id INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(train_id) REFERENCES trains(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

def save_schedule(schedule):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear previous schedule data before saving new one
    cursor.execute("DELETE FROM carriages")
    cursor.execute("DELETE FROM trains")
    conn.commit()

    for train in schedule:
        cursor.execute(
            "INSERT INTO trains (departure_time, cancelled, party_train, school_name) VALUES (?, ?, ?, ?)",
            (train['departure_time'], int(train['cancelled']), int(train['party_train']), train['school_name'])
        )
        train_id = cursor.lastrowid

        for carriage in train['carriages']:
            cursor.execute(
                "INSERT INTO carriages (train_id, number, capacity, occupied, group_size, toddlers, wheelchair, group_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    train_id,
                    carriage['number'],
                    carriage['capacity'],
                    int(carriage['occupied']),
                    carriage['group_size'],
                    carriage['toddlers'],
                    int(carriage['wheelchair']),
                    carriage['group_id']
                )
            )

    conn.commit()
    conn.close()

def load_schedule():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM trains ORDER BY departure_time")
    trains = cursor.fetchall()

    schedule = []
    for train in trains:
        cursor.execute(
            "SELECT * FROM carriages WHERE train_id = ? ORDER BY CAST(number AS INTEGER)",
            (train["id"],)
        )
        carriages = cursor.fetchall()

        schedule.append({
            "id": train["id"],
            "departure_time": train["departure_time"],
            "cancelled": bool(train["cancelled"]),
            "party_train": bool(train["party_train"]),
            "school_name": train["school_name"],
            "carriages": [
                {
                    "id": c["id"],
                    "number": c["number"],
                    "capacity": c["capacity"],
                    "occupied": bool(c["occupied"]),
                    "group_size": c["group_size"],
                    "toddlers": c["toddlers"],
                    "wheelchair": bool(c["wheelchair"]),
                    "group_id": c["group_id"],
                }
                for c in carriages
            ]
        })

    conn.close()
    return schedule

def create_notes_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_notes (
        date TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        PRIMARY KEY (date, key)
    )
    """)
    conn.commit()
    conn.close()

def create_presets_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        schedule TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

from datetime import datetime, date

def save_notes_to_db(note_date, notes_dict):
    if note_date < date.today():
        return  # Do not save past notes

    conn = get_db_connection()
    cursor = conn.cursor()
    for key, value in notes_dict.items():
        cursor.execute("""
        INSERT INTO daily_notes (date, key, value)
        VALUES (?, ?, ?)
        ON CONFLICT(date, key) DO UPDATE SET value = excluded.value
        """, (note_date.isoformat(), key, value.strip()))
    conn.commit()
    conn.close()

def load_notes_from_db(note_date, all_keys):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM daily_notes WHERE date = ?", (note_date.isoformat(),))
    rows = cursor.fetchall()
    conn.close()

    # Create a complete dict with all keys
    return {key: dict(rows).get(key, "") for key in all_keys}

def list_presets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM presets ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]

def load_preset(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT schedule FROM presets WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["schedule"])
    else:
        return None

def save_preset(name, schedule):
    conn = get_db_connection()
    cursor = conn.cursor()
    schedule_json = json.dumps(schedule)
    now = datetime.utcnow().isoformat()
    try:
        cursor.execute("INSERT INTO presets (name, schedule, created_at) VALUES (?, ?, ?)",
                       (name, schedule_json, now))
    except sqlite3.IntegrityError:
        cursor.execute("UPDATE presets SET schedule = ?, created_at = ? WHERE name = ?",
                       (schedule_json, now, name))
    conn.commit()
    conn.close()

def delete_preset(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM presets WHERE name = ?", (name,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_old_notes():
    today = date.today().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_notes WHERE date < ?", (today,))
    conn.commit()
    conn.close()

def init_custom_question_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_questions (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL
            )
        """)
        conn.commit()

def load_custom_questions():
    init_custom_question_table()
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT id, text FROM custom_questions")
        return {row[0]: row[1] for row in cursor.fetchall()}

def save_custom_question(q_id, q_text):
    init_custom_question_table()
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO custom_questions (id, text) VALUES (?, ?)", (q_id, q_text))
        conn.commit()

def delete_custom_question(q_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM custom_questions WHERE id = ?", (q_id,))
        conn.commit()