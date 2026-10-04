from datetime import datetime, timedelta
import json
from app.db.database import get_db_connection
from app.models.schemas import BreakdownRequest, ScheduleStatus
from app.core.errors import BadRequestError, ConflictError, NotFoundError, ValidationError
from app.services.simulation import get_current_time
from app.core.config import settings

def register_breakdown(req: BreakdownRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_time = get_current_time()
    
    # Validation
    cursor.execute("SELECT id FROM machines WHERE id = ?", (req.machine_id,))
    if not cursor.fetchone():
        raise NotFoundError("Machine not found")
        
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        raise ConflictError("No schedule exists")
        
    breakdown_time = current_time if current_time else datetime.now().replace(tzinfo=None)
            
    # Calculate unavailable_until
    unavail_until = None
    if req.repair_time_minutes:
        unavail_until = (breakdown_time + timedelta(minutes=req.repair_time_minutes)).isoformat()
        
    # Update machine status
    cursor.execute("""
        UPDATE machines 
        SET status = 'BROKEN_DOWN', unavailable_from = ?, unavailable_until = ?
        WHERE id = ?
    """, (breakdown_time.isoformat(), unavail_until, req.machine_id))
    
    # Record breakdown event
    cursor.execute("""
        INSERT INTO breakdown_events (machine_id, breakdown_time, repair_time_minutes, unavailable_until)
        VALUES (?, ?, ?, ?)
    """, (req.machine_id, breakdown_time.isoformat(), req.repair_time_minutes, unavail_until))
    event_id = cursor.lastrowid
    
    # Find affected orders
    # Any order on this machine that has not completed
    # (i.e. production_end > breakdown_time)
    cursor.execute("""
        SELECT work_order_id, status 
        FROM schedule_entries 
        WHERE schedule_version = ? AND machine_id = ? AND production_end > ?
    """, (s_row["version"], req.machine_id, breakdown_time.isoformat()))
    
    affected = cursor.fetchall()
    affected_ids = []
    for a in affected:
        wo_id = a["work_order_id"]
        affected_ids.append(wo_id)
        # If it was running, update status to INTERRUPTED
        if a["status"] == ScheduleStatus.RUNNING.value:
            cursor.execute("""
                UPDATE schedule_entries SET status = ?
                WHERE schedule_version = ? AND work_order_id = ?
            """, (ScheduleStatus.INTERRUPTED.value, s_row["version"], wo_id))
            
    conn.commit()
    conn.close()
    
    if req.webhook_url:
        import urllib.request
        import threading
        
        def send_webhook(url, payload):
            try:
                data = json.dumps(payload).encode('utf-8')
                request = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
                urllib.request.urlopen(request, timeout=5)
            except Exception as e:
                print(f"Failed to send webhook to {url}: {e}")
                
        payload = {
            "event": "machine_breakdown",
            "machine_id": req.machine_id,
            "breakdown_time": breakdown_time.isoformat(),
            "repair_time_minutes": req.repair_time_minutes,
            "message": f"Machine {req.machine_id} is broken down. Reschedule tasks!"
        }
        threading.Thread(target=send_webhook, args=(req.webhook_url, payload), daemon=True).start()
    
    
    return {"event_id": event_id, "affected_orders": affected_ids}

def get_affected_orders():
    # Gets the latest breakdown and its affected orders from the latest schedule
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM breakdown_events ORDER BY id DESC LIMIT 1")
    be = cursor.fetchone()
    if not be:
        conn.close()
        return []
        
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        conn.close()
        return []
        
    # Same logic
    cursor.execute("""
        SELECT work_order_id 
        FROM schedule_entries 
        WHERE schedule_version = ? AND machine_id = ? AND production_end > ?
    """, (s_row["version"], be["machine_id"], be["breakdown_time"]))
    
    affected = [r[0] for r in cursor.fetchall()]
    conn.close()
    return affected
