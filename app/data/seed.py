import json
from pathlib import Path
from app.db.database import get_db_connection

def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM machines")
    if cursor.fetchone()[0] == 0:
        machines_file = Path(__file__).parent / "machines.json"
        if machines_file.exists():
            with open(machines_file, "r") as f:
                machines = json.load(f)
                for m in machines:
                    capabilities_str = ",".join(m["capabilities"])
                    cursor.execute("""
                        INSERT INTO machines (id, name, capabilities, available_from, available_to, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (m["id"], m["name"], capabilities_str, m["available_from"], m["available_to"], m["status"]))
    
    cursor.execute("SELECT COUNT(*) FROM work_orders")
    if cursor.fetchone()[0] == 0:
        wo_file = Path(__file__).parent / "work_orders.json"
        if wo_file.exists():
            with open(wo_file, "r") as f:
                wos = json.load(f)
                for wo in wos:
                    cursor.execute("""
                        INSERT INTO work_orders (id, quantity, setup_time_minutes, processing_time_minutes, 
                        required_capability, release_time, delivery_date, priority)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (wo["id"], wo["quantity"], wo["setup_time_minutes"], wo["processing_time_minutes"],
                          wo["required_capability"], wo["release_time"], wo["delivery_date"], wo["priority"]))
    
    conn.commit()
    conn.close()
