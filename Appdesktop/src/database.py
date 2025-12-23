"""
Database - SQLite operations
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from src.config import DATABASE_PATH, PARKING_CONFIG


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def init_database():
    """Khởi tạo database và tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng thẻ RFID
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT UNIQUE NOT NULL,
            owner_name TEXT,
            plate_number TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Bảng phiên gửi xe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL,
            plate_number TEXT,
            slot_number INTEGER,
            entry_time TIMESTAMP NOT NULL,
            exit_time TIMESTAMP,
            fee INTEGER DEFAULT 0,
            payment_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Bảng slots
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number INTEGER UNIQUE NOT NULL,
            is_occupied INTEGER DEFAULT 0,
            current_session_id INTEGER
        )
    """)
    
    # Khởi tạo slots nếu chưa có
    cursor.execute("SELECT COUNT(*) FROM slots")
    if cursor.fetchone()[0] == 0:
        for i in range(1, PARKING_CONFIG["total_slots"] + 1):
            cursor.execute("INSERT INTO slots (slot_number) VALUES (?)", (i,))
    
    conn.commit()
    conn.close()


# === Card Operations ===

def add_card(card_id: str, owner_name: str = "", plate_number: str = "", phone: str = "") -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cards (card_id, owner_name, plate_number, phone) VALUES (?, ?, ?, ?)",
            (card_id, owner_name, plate_number, phone)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_card(card_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE card_id = ? AND is_active = 1", (card_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "card_id": row[1], "owner_name": row[2], "plate_number": row[3], "phone": row[4]}
    return None


def get_all_cards() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE is_active = 1 ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "card_id": r[1], "owner_name": r[2], "plate_number": r[3], "phone": r[4]} for r in rows]


def delete_card(card_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE cards SET is_active = 0 WHERE card_id = ?", (card_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# === Session Operations ===

def create_session(card_id: str, plate_number: str, slot_number: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (card_id, plate_number, slot_number, entry_time) VALUES (?, ?, ?, ?)",
        (card_id, plate_number, slot_number, datetime.now())
    )
    session_id = cursor.lastrowid
    # Đánh dấu slot đã occupied
    cursor.execute(
        "UPDATE slots SET is_occupied = 1, current_session_id = ? WHERE slot_number = ?",
        (session_id, slot_number)
    )
    conn.commit()
    conn.close()
    return session_id


def get_active_session(card_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sessions WHERE card_id = ? AND exit_time IS NULL ORDER BY entry_time DESC LIMIT 1",
        (card_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "card_id": row[1], "plate_number": row[2], "slot_number": row[3],
            "entry_time": row[4], "exit_time": row[5], "fee": row[6], "payment_status": row[7]
        }
    return None


def complete_session(session_id: int, fee: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    # Lấy slot number
    cursor.execute("SELECT slot_number FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if row:
        slot_number = row[0]
        # Update session
        cursor.execute(
            "UPDATE sessions SET exit_time = ?, fee = ?, payment_status = 'paid' WHERE id = ?",
            (datetime.now(), fee, session_id)
        )
        # Free slot
        cursor.execute(
            "UPDATE slots SET is_occupied = 0, current_session_id = NULL WHERE slot_number = ?",
            (slot_number,)
        )
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_recent_sessions(limit: int = 20) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r[0], "card_id": r[1], "plate_number": r[2], "slot_number": r[3],
        "entry_time": r[4], "exit_time": r[5], "fee": r[6], "payment_status": r[7]
    } for r in rows]


# === Slot Operations ===

def get_available_slot() -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT slot_number FROM slots WHERE is_occupied = 0 ORDER BY slot_number LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_slot_stats() -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM slots")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM slots WHERE is_occupied = 1")
    occupied = cursor.fetchone()[0]
    conn.close()
    return {"total": total, "occupied": occupied, "available": total - occupied}


def get_today_revenue() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT COALESCE(SUM(fee), 0) FROM sessions WHERE DATE(exit_time) = ? AND payment_status = 'paid'",
        (today,)
    )
    revenue = cursor.fetchone()[0]
    conn.close()
    return revenue
