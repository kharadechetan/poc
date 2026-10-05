from fastapi import APIRouter, Depends
from typing import List
import sqlite3
import json
from app.api.deps import get_db_session
from app.models.schemas import ScheduleResponse, ScheduleMetrics, RescheduleResponse, ScheduleEntry
from app.services.scheduler import generate_initial_schedule
from app.services.rescheduler import reschedule_after_breakdown
from app.core.errors import NotFoundError

router = APIRouter(prefix="/schedule", tags=["Scheduling"])

@router.post("/generate", response_model=ScheduleResponse)
def generate_schedule():
    return generate_initial_schedule()

@router.get("", response_model=ScheduleResponse)
def get_current_schedule(db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        raise NotFoundError("No schedule exists")
        
    cursor.execute("SELECT * FROM schedule_entries WHERE schedule_version = ?", (s_row["version"],))
    entries = [ScheduleEntry(**dict(r)) for r in cursor.fetchall()]
    metrics = ScheduleMetrics(**json.loads(s_row["metrics_json"]))
    
    return ScheduleResponse(schedule=entries, metrics=metrics)

@router.get("/machine-work-orders")
def get_machine_work_orders(db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        raise NotFoundError("No schedule exists")
        
    cursor.execute("SELECT machine_id, work_order_id FROM schedule_entries WHERE schedule_version = ? ORDER BY setup_start ASC", (s_row["version"],))
    entries = cursor.fetchall()
    
    result = {}
    for row in entries:
        m_id = row["machine_id"]
        w_id = row["work_order_id"]
        if m_id not in result:
            result[m_id] = {"orders": []}
        result[m_id]["orders"].append(w_id)
        
    return result

@router.get("/metrics", response_model=ScheduleMetrics)
def get_schedule_metrics(db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT metrics_json FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        raise NotFoundError("No schedule exists")
    return ScheduleMetrics(**json.loads(s_row["metrics_json"]))

@router.get("/history")
def get_schedule_history(db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM schedules ORDER BY version ASC")
    schedules = [dict(r) for r in cursor.fetchall()]
    for s in schedules:
        s["metrics"] = json.loads(s["metrics_json"])
        del s["metrics_json"]
    
    cursor.execute("SELECT * FROM rescheduling_history ORDER BY id ASC")
    history = [dict(r) for r in cursor.fetchall()]
    
    for h in history:
        h["changes"] = json.loads(h["changes_json"])
        h["reasons"] = json.loads(h["reasons_json"])
        del h["changes_json"]
        del h["reasons_json"]
        
    return {"schedules": schedules, "rescheduling_events": history}

@router.post("/reschedule", response_model=RescheduleResponse)
def reschedule():
    return reschedule_after_breakdown()

from app.services.heuristic import insert_order_dynamically

@router.post("/insert-dynamic/{work_order_id}")
def insert_dynamic(work_order_id: str):
    return insert_order_dynamically(work_order_id)
