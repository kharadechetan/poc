import json
from datetime import datetime
from app.db.database import get_db_connection
from app.models.schemas import Machine, WorkOrder, ScheduleEntry, RescheduleResponse, Change, ScheduleStatus
from app.services.optimizer import solve_schedule
from app.services.metrics import compute_metrics
from app.services.validator import validate_schedule
from app.services.simulation import get_current_time
from app.services.breakdown import get_affected_orders
from app.services.alternatives import evaluate_alternatives
from app.services.explanation import generate_rescheduling_reason
from app.core.errors import ConflictError

def reschedule_after_breakdown() -> RescheduleResponse:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM breakdown_events ORDER BY id DESC LIMIT 1")
    be = cursor.fetchone()
    if not be:
        raise ConflictError("No breakdown to reschedule")
        
    breakdown_dt = datetime.fromisoformat(be["breakdown_time"])
    
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        raise ConflictError("No schedule exists")
    old_version = s_row["version"]
    
    cursor.execute("SELECT * FROM schedule_entries WHERE schedule_version = ?", (old_version,))
    old_entries_raw = cursor.fetchall()
    old_entries = [ScheduleEntry(**dict(r)) for r in old_entries_raw]
    old_entries_by_wo = {e.work_order_id: e for e in old_entries}
    
    affected_wos = get_affected_orders()
    
    if not affected_wos:
        raise ConflictError("No affected work orders to reschedule")
        
    fixed_jobs = [e for e in old_entries if e.work_order_id not in affected_wos]
    
    cursor.execute("SELECT * FROM machines")
    machines = [Machine(**{**dict(row), 'capabilities': row['capabilities'].split(',')}) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM work_orders")
    work_orders = [WorkOrder(**dict(row)) for row in cursor.fetchall()]
    wos_by_id = {wo.id: wo for wo in work_orders}
    
    current_time = get_current_time()
    
    solver_time = max(current_time, breakdown_dt) if current_time else breakdown_dt
    
    alts = evaluate_alternatives()
    
    new_entries, status, wall_time, opt = solve_schedule(machines, work_orders, fixed_jobs, solver_time)
    
    scheduled_new = {e.work_order_id: e for e in new_entries}
    offending = [wo_id for wo_id in affected_wos if wo_id not in scheduled_new]
    
    if offending or status == "INFEASIBLE":
        raise ConflictError(f"No feasible capacity for affected orders: {offending}")
        
    validate_schedule(new_entries, machines, work_orders)
    
    metrics_before = compute_metrics(old_entries, machines, work_orders)
    metrics_after = compute_metrics(new_entries, machines, work_orders)
    
    created_at = datetime.now().isoformat()
    cursor.execute("INSERT INTO schedules (created_at, reason, metrics_json) VALUES (?, ?, ?)", 
                   (created_at, "Reschedule after breakdown", json.dumps(metrics_after.model_dump())))
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
        
    changes = []
    reasons = []
    for wo_id in affected_wos:
        o = old_entries_by_wo[wo_id]
        n = scheduled_new[wo_id]
        
        delay = int((n.production_end - o.production_end).total_seconds() / 60)
        
        c = Change(
            work_order_id=wo_id,
            from_machine=o.machine_id,
            to_machine=n.machine_id,
            old_start=o.setup_start,
            old_end=o.production_end,
            new_start=n.setup_start,
            new_end=n.production_end,
            delay_delta_minutes=delay
        )
        changes.append(c)
        
        was_interrupted = (o.status == ScheduleStatus.INTERRUPTED)
        
        r = generate_rescheduling_reason(
            wo_id=wo_id,
            old_m=o.machine_id,
            new_m=n.machine_id,
            breakdown_time=breakdown_dt,
            capability=wos_by_id[wo_id].required_capability,
            old_start=o.setup_start,
            old_end=o.production_end,
            new_start=n.setup_start,
            new_end=n.production_end,
            old_late=o.lateness_minutes,
            new_late=n.lateness_minutes,
            priority=wos_by_id[wo_id].priority,
            was_interrupted=was_interrupted,
            alternatives=alts.get(wo_id, [])
        )
        reasons.append(r)
        
    cursor.execute("""
        INSERT INTO rescheduling_history (breakdown_event_id, schedule_version, changes_json, reasons_json)
        VALUES (?, ?, ?, ?)
    """, (be["id"], new_version, json.dumps([c.model_dump(mode='json') for c in changes]), json.dumps([r.model_dump(mode='json') for r in reasons])))
    
    conn.commit()
    conn.close()
    
    return RescheduleResponse(
        old_schedule=old_entries,
        breakdown_event=dict(be),
        affected_work_orders=affected_wos,
        alternatives_evaluated=alts,
        new_schedule=new_entries,
        changes=changes,
        optimization_metrics_before=metrics_before,
        optimization_metrics_after=metrics_after,
        reasons=reasons
    )
