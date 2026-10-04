from fastapi import APIRouter, Depends
from typing import List
import sqlite3
from app.api.deps import get_db_session
from app.models.schemas import WorkOrder, WorkOrderCreate
from app.core.errors import NotFoundError, ConflictError, ValidationError

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

@router.get("", response_model=List[WorkOrder])
def get_work_orders(db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM work_orders")
    return [WorkOrder(**dict(row)) for row in cursor.fetchall()]

@router.get("/{work_order_id}", response_model=WorkOrder)
def get_work_order(work_order_id: str, db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM work_orders WHERE id = ?", (work_order_id,))
    row = cursor.fetchone()
    if not row:
        raise NotFoundError("Work Order not found")
    return WorkOrder(**dict(row))

@router.post("", response_model=WorkOrder)
def create_work_order(wo: WorkOrderCreate, db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM work_orders WHERE id = ?", (wo.id,))
    if cursor.fetchone():
        raise ConflictError("Work Order ID already exists")
        
    cursor.execute("SELECT id, capabilities FROM machines")
    valid_caps = set()
    for row in cursor.fetchall():
        for cap in row["capabilities"].split(","):
            valid_caps.add(cap)
            
    if wo.required_capability not in valid_caps:
        raise ValidationError(f"Required capability {wo.required_capability} is not supported by any machine")
        
    from datetime import datetime, timedelta
    from app.services.simulation import get_current_time
    
    release_time = get_current_time()
    if not release_time:
        release_time = datetime.now().replace(tzinfo=None, second=0, microsecond=0)
        
    delivery_date = (release_time + timedelta(days=3)).date()
        
    cursor.execute("""
        INSERT INTO work_orders (id, quantity, setup_time_minutes, processing_time_minutes, 
        required_capability, release_time, delivery_date, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (wo.id, wo.quantity, wo.setup_time_minutes, wo.processing_time_minutes,
          wo.required_capability, release_time.isoformat(), delivery_date.isoformat(), wo.priority.value))
    db.commit()
    return get_work_order(wo.id, db)
