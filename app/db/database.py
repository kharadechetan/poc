import sqlite3
from typing import Iterator
from app.core.config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS machines (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        capabilities TEXT NOT NULL,
        available_from TEXT NOT NULL,
        available_to TEXT NOT NULL,
        status TEXT NOT NULL,
        unavailable_from TEXT,
        unavailable_until TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS work_orders (
        id TEXT PRIMARY KEY,
        quantity INTEGER NOT NULL,
        setup_time_minutes INTEGER NOT NULL,
        processing_time_minutes INTEGER NOT NULL,
        required_capability TEXT NOT NULL,
        release_time TEXT NOT NULL,
        delivery_date TEXT NOT NULL,
        priority TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        version INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        reason TEXT,
        metrics_json TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_version INTEGER NOT NULL,
        work_order_id TEXT NOT NULL,
        machine_id TEXT NOT NULL,
        setup_start TEXT NOT NULL,
        production_start TEXT NOT NULL,
        production_end TEXT NOT NULL,
        setup_duration_minutes INTEGER NOT NULL,
        processing_duration_minutes INTEGER NOT NULL,
        priority TEXT NOT NULL,
        delivery_date TEXT NOT NULL,
        status TEXT NOT NULL,
        lateness_minutes INTEGER NOT NULL,
        FOREIGN KEY (schedule_version) REFERENCES schedules (version)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_state (
        id INTEGER PRIMARY KEY,
        sim_time TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS breakdown_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_id TEXT NOT NULL,
        breakdown_time TEXT NOT NULL,
        repair_time_minutes INTEGER,
        unavailable_until TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rescheduling_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        breakdown_event_id INTEGER,
        schedule_version INTEGER,
        changes_json TEXT,
        reasons_json TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = [
        "machines", "work_orders", "schedules", "schedule_entries", 
        "simulation_state", "breakdown_events", "rescheduling_history"
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()
    init_db()

def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
