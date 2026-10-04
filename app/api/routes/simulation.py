from fastapi import APIRouter, Depends, Body
from typing import List, Dict, Optional
import sqlite3
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.api.deps import get_db_session
from app.models.schemas import SimulationStateResponse, BreakdownRequest, ScheduleStatus, FlexibleModel
from app.services.simulation import get_current_time, set_current_time, update_job_states
from app.services.breakdown import register_breakdown, get_affected_orders
from app.services.alternatives import evaluate_alternatives
from app.core.config import settings
from app.core.errors import ConflictError, BadRequestError

router = APIRouter(prefix="/simulation", tags=["Simulation"])

@router.post("/start")
def start_simulation(db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    if not cursor.fetchone():
        raise ConflictError("No schedule exists")
        
    st = datetime.now().replace(second=0, microsecond=0, tzinfo=None)
    set_current_time(st)
    return {"message": "Simulation started", "current_time": st}

class AdvanceSimReq(FlexibleModel):
    minutes: int = Field(gt=0)

@router.post("/advance")
def advance_simulation(req: AdvanceSimReq, db: sqlite3.Connection = Depends(get_db_session)):
    current = get_current_time()
    if not current:
        raise ConflictError("Simulation not started")
        
    new_time = current + timedelta(minutes=req.minutes)
        
    set_current_time(new_time)
    return {"message": "Simulation advanced", "current_time": new_time}

@router.get("/state", response_model=SimulationStateResponse)
def get_simulation_state(db: sqlite3.Connection = Depends(get_db_session)):
    current = get_current_time()
    if not current:
        raise ConflictError("Simulation not started")
        
    cursor = db.cursor()
    cursor.execute("SELECT version FROM schedules ORDER BY version DESC LIMIT 1")
    s_row = cursor.fetchone()
    if not s_row:
        raise ConflictError("No schedule exists")
        
    cursor.execute("SELECT work_order_id, machine_id, status FROM schedule_entries WHERE schedule_version = ?", (s_row["version"],))
    entries = cursor.fetchall()
    
    order_states = {}
    running = {}
    occupied = []
    completed = []
    waiting = []
    
    cursor.execute("SELECT id FROM machines")
    all_m = [r["id"] for r in cursor.fetchall()]
    
    for e in entries:
        st = ScheduleStatus(e["status"])
        order_states[e["work_order_id"]] = st
        if st == ScheduleStatus.RUNNING:
            running[e["machine_id"]] = e["work_order_id"]
            occupied.append(e["machine_id"])
        elif st == ScheduleStatus.COMPLETED:
            completed.append(e["work_order_id"])
        elif st == ScheduleStatus.WAITING:
            waiting.append(e["work_order_id"])
            
    free = [m for m in all_m if m not in occupied]
    
    return SimulationStateResponse(
        current_time=current,
        order_states=order_states,
        running_orders_per_machine={m: running.get(m) for m in all_m},
        occupied_machines=occupied,
        free_machines=free,
        completed_orders=completed,
        waiting_orders=waiting
    )

@router.post("/breakdown")
def simulate_breakdown(req: BreakdownRequest):
    return register_breakdown(req)

@router.get("/affected-orders", response_model=List[str])
def get_affected():
    return get_affected_orders()

@router.get("/alternatives")
def get_alternatives():
    return evaluate_alternatives()
