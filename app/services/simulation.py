from datetime import datetime
from app.db.database import get_db_connection
from app.models.schemas import ScheduleStatus

def get_current_time() -> datetime:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sim_time FROM simulation_state ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return datetime.fromisoformat(row["sim_time"])
    return None

def set_current_time(dt: datetime):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM simulation_state ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE simulation_state SET sim_time = ? WHERE id = ?", (dt.isoformat(), row["id"]))
    else:
        cursor.execute("INSERT INTO simulation_state (sim_time) VALUES (?)", (dt.isoformat(),))
    conn.commit()
    
    # Update job states based on new time
    update_job_states(dt, conn)
    conn.close()

def update_job_states(current_time: datetime, conn=None):
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
        
    cursor = conn.cursor()
    
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        if close_conn: conn.close()
        return
        
    version = row["version"]
    
    cursor.execute("""
        SELECT id, setup_start, production_end, status 
        FROM schedule_entries 
        WHERE schedule_version = ?
    """, (version,))
    
    entries = cursor.fetchall()
    
    for entry in entries:
        start = datetime.fromisoformat(entry["setup_start"])
        end = datetime.fromisoformat(entry["production_end"])
        status = entry["status"]
        
        if status in [ScheduleStatus.WAITING.value, ScheduleStatus.RUNNING.value]:
            new_status = status
            if current_time >= end:
                new_status = ScheduleStatus.COMPLETED.value
            elif current_time >= start:
                new_status = ScheduleStatus.RUNNING.value
                
            if new_status != status:
                cursor.execute("""
                    UPDATE schedule_entries 
                    SET status = ? 
                    WHERE id = ?
                """, (new_status, entry["id"]))
    
    conn.commit()
    if close_conn:
        conn.close()
