from datetime import datetime, timedelta
from app.db.database import get_db_connection
from app.services.breakdown import get_affected_orders
from app.models.schemas import Machine, WorkOrder, ScheduleEntry

def evaluate_alternatives():
    affected = get_affected_orders()
    if not affected:
        return {}
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM machines")
    machines = [Machine(**{**dict(row), 'capabilities': row['capabilities'].split(',')}) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM work_orders WHERE id IN ({})".format(','.join('?'*len(affected))), affected)
    wos = {r["id"]: WorkOrder(**dict(r)) for r in cursor.fetchall()}
    
    cursor.execute("SELECT * FROM breakdown_events ORDER BY id DESC LIMIT 1")
    be = cursor.fetchone()
    breakdown_dt = datetime.fromisoformat(be["breakdown_time"])
    
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    s_version = cursor.fetchone()["version"]
    
    cursor.execute("SELECT * FROM schedule_entries WHERE schedule_version = ?", (s_version,))
    entries = [ScheduleEntry(**dict(r)) for r in cursor.fetchall()]
    
    results = {}
    
    for wo_id in affected:
        wo = wos[wo_id]
        wo_alts = []
        
        for m in machines:
            if wo.required_capability not in m.capabilities:
                wo_alts.append({
                    "machine_id": m.id,
                    "feasible": False,
                    "reject_reason": f"Incompatible capability. Requires {wo.required_capability}"
                })
                continue
                
            if m.status in ["UNAVAILABLE", "BROKEN_DOWN"]:
                # If broken forever, or broken until later
                wo_alts.append({
                    "machine_id": m.id,
                    "feasible": False,
                    "reject_reason": f"Machine is {m.status}"
                })
                continue
                
            # Estimate when it's free
            # Find the latest job scheduled on this machine
            m_jobs = [e for e in entries if e.machine_id == m.id and e.work_order_id not in affected]
            if m_jobs:
                latest_end = max(e.production_end for e in m_jobs)
                free_from = max(latest_end, breakdown_dt, wo.release_time)
            else:
                free_from = max(breakdown_dt, wo.release_time)
                
            dur = wo.setup_time_minutes + wo.processing_time_minutes
            # Simple estimate: free_from + dur
            est_completion = free_from + timedelta(minutes=dur)
            due_dt = datetime.combine(wo.delivery_date, datetime.strptime("17:00", "%H:%M").time())
            
            late_mins = max(0, int((est_completion - due_dt).total_seconds() / 60))
            
            wo_alts.append({
                "machine_id": m.id,
                "feasible": True,
                "available_from": free_from.isoformat(),
                "estimated_completion": est_completion.isoformat(),
                "expected_lateness_minutes": late_mins,
                "reject_reason": None
            })
            
        results[wo_id] = wo_alts
        
    conn.close()
    return results
