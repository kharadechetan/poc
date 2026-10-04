import json
from datetime import datetime, timedelta
from typing import List, Dict

from app.db.database import get_db_connection
from app.models.schemas import Machine, WorkOrder, ScheduleEntry, ScheduleStatus
from app.services.simulation import get_current_time
from app.services.metrics import compute_metrics
from app.core.errors import ConflictError, NotFoundError

def insert_order_dynamically(work_order_id: str) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Get the new work order
    cursor.execute("SELECT * FROM work_orders WHERE id = ?", (work_order_id,))
    wo_row = cursor.fetchone()
    if not wo_row:
        raise NotFoundError(f"Work order {work_order_id} not found")
    wo = WorkOrder(**dict(wo_row))
    
    # 2. Get the active schedule version
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        raise ConflictError("No active schedule to insert into. Generate an initial schedule first.")
    active_version = s_row["version"]
    
    # 3. Check if it is already scheduled
    cursor.execute("SELECT * FROM schedule_entries WHERE schedule_version = ? AND work_order_id = ?", (active_version, work_order_id))
    if cursor.fetchone():
        raise ConflictError(f"Work order {work_order_id} is already in the active schedule.")
        
    # 4. Fetch all active entries to calculate load
    cursor.execute("SELECT * FROM schedule_entries WHERE schedule_version = ?", (active_version,))
    old_entries_raw = cursor.fetchall()
    old_entries = [ScheduleEntry(**dict(r)) for r in old_entries_raw]
    
    # 5. Fetch all healthy machines
    cursor.execute("SELECT * FROM machines WHERE status = 'AVAILABLE'")
    machines = [Machine(**{**dict(row), 'capabilities': row['capabilities'].split(',')}) for row in cursor.fetchall()]
    
    # Filter machines by capability
    compatible_machines = [m for m in machines if wo.required_capability in m.capabilities]
    if not compatible_machines:
        raise ConflictError(f"No available machines have the capability: {wo.required_capability}")
        
    current_time = get_current_time()
    if not current_time:
        raise ConflictError("Simulation has not started.")
        
    # 6. Calculate total workload (end time of the last job) for each compatible machine
    machine_loads = {m.id: max(current_time, datetime.combine(wo.delivery_date, m.available_from)) for m in compatible_machines}
    machine_objs = {m.id: m for m in compatible_machines}
    
    for entry in old_entries:
        if entry.machine_id in machine_loads:
            # We only care about jobs that are NOT completed, but checking the absolute latest production_end is safest
            if entry.production_end > machine_loads[entry.machine_id]:
                machine_loads[entry.machine_id] = entry.production_end
                
    # 7. Pick the machine with the earliest availability (Least Work Remaining)
    best_machine_id = min(machine_loads, key=machine_loads.get)
    best_machine = machine_objs[best_machine_id]
    start_time = machine_loads[best_machine_id]
    
    # 8. Create the new schedule entry
    setup_duration = wo.setup_time_minutes
    processing_duration = wo.processing_time_minutes
    
    production_start = start_time + timedelta(minutes=setup_duration)
    production_end = production_start + timedelta(minutes=processing_duration)
    
    # Check lateness
    delivery_datetime = datetime.combine(wo.delivery_date, datetime.min.time())
    lateness = max(0, int((production_end - delivery_datetime).total_seconds() / 60))
    
    new_entry = ScheduleEntry(
        work_order_id=wo.id,
        machine_id=best_machine.id,
        setup_start=start_time,
        production_start=production_start,
        production_end=production_end,
        setup_duration_minutes=setup_duration,
        processing_duration_minutes=processing_duration,
        priority=wo.priority,
        delivery_date=wo.delivery_date,
        status=ScheduleStatus.WAITING,
        lateness_minutes=lateness
    )
    
    new_entries = old_entries + [new_entry]
    
    # 9. Fetch all work orders for metrics
    cursor.execute("SELECT * FROM work_orders")
    all_wos = [WorkOrder(**dict(row)) for row in cursor.fetchall()]
    
    # 10. Save as a NEW schedule version
    metrics = compute_metrics(new_entries, machines, all_wos)
    created_at = datetime.now().isoformat()
    reason_str = f"Dynamically inserted new order {wo.id} via Load-Balancing Heuristic"
    
    cursor.execute("INSERT INTO schedules (created_at, reason, metrics_json) VALUES (?, ?, ?)", 
                   (created_at, reason_str, json.dumps(metrics.model_dump())))
    new_version = cursor.lastrowid
    
    for e in new_entries:
        cursor.execute("""
            INSERT INTO schedule_entries (
                schedule_version, work_order_id, machine_id, setup_start, production_start, production_end,
                setup_duration_minutes, processing_duration_minutes, priority, delivery_date, status, lateness_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_version, e.work_order_id, e.machine_id, e.setup_start.isoformat(), e.production_start.isoformat(),
            e.production_end.isoformat(), e.setup_duration_minutes, e.processing_duration_minutes,
            e.priority.value, e.delivery_date.isoformat(), e.status.value, e.lateness_minutes
        ))
        
    conn.commit()
    conn.close()
    
    rationale = (f"Order {wo.id} requires '{wo.required_capability}'. "
                 f"Evaluated {len(compatible_machines)} compatible machines. "
                 f"Assigned to {best_machine.id} because it had the shortest queue (least work remaining). "
                 f"It will start at {start_time.isoformat()} and end at {production_end.isoformat()}.")
                 
    return {
        "message": "Dynamic insertion successful",
        "assigned_machine": best_machine.id,
        "new_entry": new_entry,
        "rationale": rationale
    }
