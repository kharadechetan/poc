from fastapi import APIRouter, Depends
from typing import List
import sqlite3
from app.api.deps import get_db_session
from app.models.schemas import Machine, MachineCreate
from app.core.errors import NotFoundError, ConflictError

router = APIRouter(prefix="/machines", tags=["Machines"])

@router.get("", response_model=List[Machine])
def get_machines(db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM machines")
    return [Machine(**{**dict(row), 'capabilities': row['capabilities'].split(',')}) for row in cursor.fetchall()]

@router.get("/{machine_id}", response_model=Machine)
def get_machine(machine_id: str, db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM machines WHERE id = ?", (machine_id,))
    row = cursor.fetchone()
    if not row:
        raise NotFoundError("Machine not found")
    return Machine(**{**dict(row), 'capabilities': row['capabilities'].split(',')})

@router.post("", response_model=Machine)
def create_machine(machine: MachineCreate, db: sqlite3.Connection = Depends(get_db_session)):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM machines WHERE id = ?", (machine.id,))
    if cursor.fetchone():
        raise ConflictError("Machine ID already exists")
    
    cap_str = ",".join(machine.capabilities)
    
    cursor.execute("""
        INSERT INTO machines (id, name, capabilities, available_from, available_to, status, unavailable_from, unavailable_until)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (machine.id, machine.name, cap_str, machine.available_from.strftime("%H:%M"), machine.available_to.strftime("%H:%M"), 
          machine.status.value, machine.unavailable_from.isoformat() if machine.unavailable_from else None, 
          machine.unavailable_until.isoformat() if machine.unavailable_until else None))
    db.commit()
    return get_machine(machine.id, db)
