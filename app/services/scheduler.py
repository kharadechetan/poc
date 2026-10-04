import json
from datetime import datetime
from app.db.database import get_db_connection
from app.models.schemas import Machine, WorkOrder, ScheduleResponse
from app.services.optimizer import solve_schedule
from app.services.metrics import compute_metrics
from app.services.validator import validate_schedule
from app.services.simulation import get_current_time

def generate_initial_schedule() -> ScheduleResponse:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM machines")
    machines = [Machine(**{**dict(row), 'capabilities': row['capabilities'].split(',')}) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM work_orders")
    work_orders = [WorkOrder(**dict(row)) for row in cursor.fetchall()]
    
    current_time = get_current_time()
    
    schedule_entries, status, wall_time, opt = solve_schedule(machines, work_orders, [], current_time)
    
    validate_schedule(schedule_entries, machines, work_orders)
    
    metrics = compute_metrics(schedule_entries, machines, work_orders)
    
    created_at = datetime.now().isoformat()
    cursor.execute("INSERT INTO schedules (created_at, reason, metrics_json) VALUES (?, ?, ?)", 
                   (created_at, "Initial generation", json.dumps(metrics.model_dump())))
    version = cursor.lastrowid
    
    for e in schedule_entries:
        cursor.execute("""
            INSERT INTO schedule_entries (
                schedule_version, work_order_id, machine_id, setup_start, production_start, production_end,
                setup_duration_minutes, processing_duration_minutes, priority, delivery_date, status, lateness_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version, e.work_order_id, e.machine_id, e.setup_start.isoformat(), e.production_start.isoformat(),
            e.production_end.isoformat(), e.setup_duration_minutes, e.processing_duration_minutes,
            e.priority.value, e.delivery_date.isoformat(), e.status.value, e.lateness_minutes
        ))
        
    conn.commit()
    conn.close()
    
    return ScheduleResponse(schedule=schedule_entries, metrics=metrics)
