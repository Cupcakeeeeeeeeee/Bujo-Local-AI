import sqlite3
import os
import json

DB_PATH = os.environ.get("BUJO_DB_PATH", os.path.join(os.path.dirname(__file__), "assistant.db"))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

# 1. KULLANICI PROFİLİ TABLOSU (gender sütunu eklendi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            gender TEXT,               -- 'Erkek', 'Kadın', 'Belirtmek İstemiyorum'
            birth_date TEXT,
            height REAL,
            weight REAL,
            occupation TEXT,
            hobbies TEXT,
            about_me TEXT,
            assistant_style TEXT,
            response_length TEXT,
            ai_rules TEXT,
            communication_style TEXT
        )
    """)

    # 2. MODÜLLER
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_modules (
            module_key TEXT PRIMARY KEY,
            is_active INTEGER DEFAULT 1
        )
    """)

    # 3. SU TAKİBİ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount_ml INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. KALORİ TAKİBİ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calorie_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_name TEXT NOT NULL,
            calories INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. ÖZEL TAKİPÇİLER
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_trackers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            unit TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_tracker_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracker_id INTEGER,
            value REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tracker_id) REFERENCES custom_trackers(id)
        )
    """)

    # 6. GÜNLÜK NOTLARI
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. TAKVİM & ETKİNLİK
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. KİTAP & DİZİ & FİLM TAKİBİ (status sütunu eklendi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            media_type TEXT NOT NULL,  -- 'Kitap', 'Film', 'Dizi'
            creator TEXT,
            rating INTEGER DEFAULT 0,
            review TEXT,
            status TEXT DEFAULT 'Tamamlandı', -- 'Tamamlandı' veya 'İstek Listesi'
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 9. SOHBET
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )
    """)

    # 10. STICKER DEPOSU & SAYFA SÜSLEMELERİ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sticker_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_str TEXT NOT NULL,
            sticker_key TEXT NOT NULL,
            category TEXT DEFAULT 'cute',
            pos_x REAL DEFAULT 50.0,
            pos_y REAL DEFAULT 50.0,
            scale REAL DEFAULT 1.0,
            rotation INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 11. ADET DÖNGÜSÜ TAKİBİ (OPSİYONEL)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS period_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            cycle_length INTEGER DEFAULT 28,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# --- PROFİL ---
def save_profile_db(profile_dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_profile")
    cursor.execute("""
        INSERT INTO user_profile (name, gender, birth_date, height, weight, occupation, hobbies, about_me, assistant_style, response_length, ai_rules, communication_style)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile_dict.get("name"),
        profile_dict.get("gender", "Belirtmek İstemiyorum"),
        profile_dict.get("birth_date"),
        profile_dict.get("height"),
        profile_dict.get("weight"),
        profile_dict.get("occupation"),
        json.dumps(profile_dict.get("hobbies", []), ensure_ascii=False),
        profile_dict.get("about_me"),
        profile_dict.get("assistant_style"),
        profile_dict.get("response_length", "Kısa & Öz"),
        profile_dict.get("ai_rules", ""),
        profile_dict.get("assistant_style")
    ))
    conn.commit()
    conn.close()

def get_profile_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        data["hobbies"] = json.loads(data["hobbies"]) if data["hobbies"] else []
        return data
    return None

# --- MODÜLLER ---
def set_module_status(module_key, is_active):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO active_modules (module_key, is_active) 
        VALUES (?, ?) 
        ON CONFLICT(module_key) DO UPDATE SET is_active=excluded.is_active
    """, (module_key, 1 if is_active else 0))
    conn.commit()
    conn.close()

def get_active_modules():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT module_key, is_active FROM active_modules")
    rows = cursor.fetchall()
    conn.close()
    
    defaults = {"water": True, "calorie": True, "schedule": True, "media": True, "period": False}
    for row in rows:
        defaults[row["module_key"]] = bool(row["is_active"])
    return defaults

# --- SU ---
def add_water(amount_ml):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO water_tracker (amount_ml) VALUES (?)", (amount_ml,))
    conn.commit()
    conn.close()

def get_today_water_entries():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount_ml, strftime('%H:%M', date, 'localtime') as time FROM water_tracker WHERE DATE(date) = DATE('now', 'localtime') ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_water_entry(entry_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM water_tracker WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# --- KALORİ ---
def add_calorie(food_name, calories):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO calorie_tracker (food_name, calories) VALUES (?, ?)", (food_name, calories))
    conn.commit()
    conn.close()

def get_today_calorie_entries():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, food_name, calories, strftime('%H:%M', date, 'localtime') as time FROM calorie_tracker WHERE DATE(date) = DATE('now', 'localtime') ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_calorie_entry(entry_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM calorie_tracker WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# --- GÜNLÜK NOTLARI ---
def add_diary_entry(content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO diary_entries (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()

def get_today_diary_entries():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, strftime('%H:%M', date, 'localtime') as time FROM diary_entries WHERE DATE(date) = DATE('now', 'localtime') ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_diary_entry(entry_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# --- ÖZEL TAKİPÇİLER ---
def add_custom_tracker(name, unit):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO custom_trackers (name, unit) VALUES (?, ?)", (name, unit))
        conn.commit()
        res = True
    except sqlite3.IntegrityError:
        res = False
    conn.close()
    return res

def get_all_custom_trackers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_trackers")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_custom_entry(tracker_id, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO custom_tracker_entries (tracker_id, value) VALUES (?, ?)", (tracker_id, value))
    conn.commit()
    conn.close()

def get_today_custom_entries(tracker_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.value, strftime('%H:%M', e.date, 'localtime') as time 
        FROM custom_tracker_entries e 
        WHERE e.tracker_id = ? AND DATE(e.date) = DATE('now', 'localtime')
        ORDER BY e.id DESC
    """, (tracker_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_custom_entry(entry_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM custom_tracker_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# --- TAKVİM & ETKİNLİK ---
def add_schedule_event(title, event_date, description=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO schedule_tracker (title, event_date, description) VALUES (?, ?, ?)", (title, str(event_date), description))
    conn.commit()
    conn.close()

def update_schedule_event(event_id, title, event_date, description=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE schedule_tracker SET title=?, event_date=?, description=? WHERE id=?", (title, str(event_date), description, event_id))
    conn.commit()
    conn.close()

def get_events_for_month(year, month):
    conn = get_connection()
    cursor = conn.cursor()
    month_str = f"{year}-{month:02d}"
    cursor.execute("SELECT * FROM schedule_tracker WHERE strftime('%Y-%m', event_date) = ? ORDER BY event_date ASC", (month_str,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_upcoming_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedule_tracker WHERE DATE(event_date) >= DATE('now', 'localtime') ORDER BY event_date ASC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_schedule_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedule_tracker WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

# --- MEDYA (ÇİFTE KAYIT KORUMALI & DÜZENLEMELİ) ---
def add_or_update_media_entry(title, media_type, creator="", rating=0, review="", status="Tamamlandı"):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Eser veritabanında var mı kontrol et (İsim ve tür bazlı)
    cursor.execute("SELECT id FROM media_tracker WHERE LOWER(title) = LOWER(?) AND media_type = ?", (title.strip(), media_type))
    existing = cursor.fetchone()

    if existing:
        # Varsa Güncelle (Çifte kayıt engelleme)
        cursor.execute("""
            UPDATE media_tracker 
            SET creator=?, rating=?, review=?, status=?
            WHERE id=?
        """, (creator, rating, review, status, existing["id"]))
    else:
        # Yoksa Sıfırdan Ekle
        cursor.execute("""
            INSERT INTO media_tracker (title, media_type, creator, rating, review, status) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title.strip(), media_type, creator, rating, review, status))

    conn.commit()
    conn.close()

def update_media_entry(media_id, title, media_type, creator="", rating=0, review="", status="Tamamlandı"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE media_tracker 
        SET title=?, media_type=?, creator=?, rating=?, review=?, status=?
        WHERE id=?
    """, (title, media_type, creator, rating, review, status, media_id))
    conn.commit()
    conn.close()

def get_all_media():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT *, strftime('%Y-%m-%d', date, 'localtime') as date_str FROM media_tracker ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_media_entry(media_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM media_tracker WHERE id = ?", (media_id,))
    conn.commit()
    conn.close()

# --- SOHBET ---
def create_chat_session(title="Yeni Sohbet"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_sessions (title) VALUES (?)", (title,))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def update_chat_session_title(session_id, new_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (new_title, session_id))
    conn.commit()
    conn.close()

def get_all_chat_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_sessions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_chat_message(session_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()

def get_chat_messages(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_chat_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

# --- GÜN ÖZETİ ---
# database/db_manager.py dosyasının en altındaki fonksiyon:

def get_day_summary(date_str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(amount_ml) as total FROM water_tracker WHERE DATE(date) = DATE(?)", (date_str,))
    water = cursor.fetchone()["total"] or 0

    # DÜZELTİLEN SATIR: 'id' sütununu da sorguya ekledik! (SELECT id, food_name, calories...)
    cursor.execute("SELECT id, food_name, calories FROM calorie_tracker WHERE DATE(date) = DATE(?)", (date_str,))
    calories = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM diary_entries WHERE DATE(date) = DATE(?)", (date_str,))
    diaries = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM schedule_tracker WHERE DATE(event_date) = DATE(?) ORDER BY event_date ASC", (date_str,))
    events = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM media_tracker WHERE DATE(date) = DATE(?)", (date_str,))
    media = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM sticker_entries WHERE DATE(date_str) = DATE(?) ORDER BY id ASC", (date_str,))
    stickers = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "water_ml": water,
        "calories": calories,
        "diaries": diaries,
        "events": events,
        "media": media,
        "stickers": stickers
    }

def delete_schedule_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedule_tracker WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

# --- STICKER YÖNETİMİ ---
def add_sticker_entry(date_str, sticker_key, category="cute", pos_x=50.0, pos_y=50.0, scale=1.0, rotation=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sticker_entries (date_str, sticker_key, category, pos_x, pos_y, scale, rotation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(date_str), sticker_key, category, float(pos_x), float(pos_y), float(scale), int(rotation)))
    sticker_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sticker_id

def update_sticker_position(sticker_id, pos_x, pos_y):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sticker_entries SET pos_x = ?, pos_y = ? WHERE id = ?", (float(pos_x), float(pos_y), sticker_id))
    conn.commit()
    conn.close()

def update_sticker_scale(sticker_id, scale):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sticker_entries SET scale = ? WHERE id = ?", (float(scale), sticker_id))
    conn.commit()
    conn.close()

def get_stickers_for_date(date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sticker_entries WHERE date_str = ? OR DATE(date_str) = DATE(?) ORDER BY id ASC", (str(date_str), str(date_str)))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_sticker_entry(sticker_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sticker_entries WHERE id = ?", (sticker_id,))
    conn.commit()
    conn.close()

def clear_stickers_for_date(date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sticker_entries WHERE date_str = ? OR DATE(date_str) = DATE(?)", (str(date_str), str(date_str)))
    conn.commit()
    conn.close()

# --- ADET DÖNGÜSÜ TAKİBİ ---
def add_period_entry(start_date, end_date=None, cycle_length=28, notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO period_tracker (start_date, end_date, cycle_length, notes)
        VALUES (?, ?, ?, ?)
    """, (str(start_date), str(end_date) if end_date else None, int(cycle_length), notes))
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return entry_id

def get_latest_period_entry():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM period_tracker ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_period_entries():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM period_tracker ORDER BY start_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_period_entry(entry_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM period_tracker WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()