from datetime import date, datetime, time
from enum import Enum
from typing import Dict, List, Optional, Any
import re

from pydantic import BaseModel, Field, model_validator

def parse_flexible_datetime_string(val: str) -> str:
    if not isinstance(val, str):
        return val
    # Match DD,MM,YYYY or DD/MM/YYYY with optional time
    m = re.match(r"^(\d{1,2})[,\/](\d{1,2})[,\/](\d{4})(?:[ T](\d{1,2})[:,](\d{1,2})(?:[:,](\d{1,2}))?)?$", val)
    if m:
        d, mo, y, h, mn, s = m.groups()
        res = f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
        if h and mn:
            res += f"T{h.zfill(2)}:{mn.zfill(2)}:{s.zfill(2) if s else '00'}"
        return res
    # Match HH,MM or HH:MM
    m2 = re.match(r"^(\d{1,2})[,:](\d{1,2})$", val)
    if m2:
        h, mn = m2.groups()
        return f"{h.zfill(2)}:{mn.zfill(2)}:00"
    return val

class FlexibleModel(BaseModel):
    @model_validator(mode='before')
    @classmethod
    def clean_flexible_dates(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = parse_flexible_datetime_string(v)
        return data

class Priority(str, Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class MachineStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    BROKEN_DOWN = "BROKEN_DOWN"

class ScheduleStatus(str, Enum):
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"
    RESCHEDULED = "RESCHEDULED"

class Machine(FlexibleModel):
    id: str = Field(pattern=r"^M\d{3}$")
    name: str
    capabilities: List[str] = Field(min_length=1)
    available_from: time
    available_to: time
    status: MachineStatus = MachineStatus.AVAILABLE
    unavailable_from: Optional[datetime] = None
    unavailable_until: Optional[datetime] = None

class WorkOrder(FlexibleModel):
    id: str = Field(pattern=r"^WO-\d{3}$")
    quantity: int = Field(gt=0)
    setup_time_minutes: int = Field(gt=0)
    processing_time_minutes: int = Field(gt=0)
    required_capability: str
    release_time: datetime
    delivery_date: date
    priority: Priority

class ScheduleEntry(FlexibleModel):
    work_order_id: str
    machine_id: str
    setup_start: datetime
    production_start: datetime
    production_end: datetime
    setup_duration_minutes: int
    processing_duration_minutes: int
    priority: Priority
    delivery_date: date
    status: ScheduleStatus
    lateness_minutes: int

class ScheduleMetrics(FlexibleModel):
    scheduled_orders: int
    unscheduled_orders: List[str]
    total_completion_time_minutes: int
    makespan_minutes: int
    total_lateness_minutes: int
    number_of_late_orders: int
    weighted_lateness: int
    machine_utilization: Dict[str, float]
    overall_machine_utilization: float
    objective_value: int

class ScheduleResponse(FlexibleModel):
    schedule: List[ScheduleEntry]
    metrics: ScheduleMetrics

class SimulationStateResponse(FlexibleModel):
    current_time: datetime
    order_states: Dict[str, ScheduleStatus]
    running_orders_per_machine: Dict[str, Optional[str]]
    occupied_machines: List[str]
    free_machines: List[str]
    completed_orders: List[str]
    waiting_orders: List[str]

class BreakdownRequest(FlexibleModel):
    machine_id: str
    repair_time_minutes: int = Field(gt=0)
    webhook_url: Optional[str] = None

class Change(FlexibleModel):
    work_order_id: str
    from_machine: str
    to_machine: str
    old_start: datetime
    old_end: datetime
    new_start: datetime
    new_end: datetime
    delay_delta_minutes: int

class Reason(FlexibleModel):
    work_order_id: str
    reason: str

class RescheduleResponse(FlexibleModel):
    old_schedule: List[ScheduleEntry]
    breakdown_event: Dict
    affected_work_orders: List[str]
    alternatives_evaluated: Dict
    new_schedule: List[ScheduleEntry]
    changes: List[Change]
    optimization_metrics_before: ScheduleMetrics
    optimization_metrics_after: ScheduleMetrics
    reasons: List[Reason]

class MachineCreate(Machine):
    pass

class WorkOrderCreate(FlexibleModel):
    id: str = Field(pattern=r"^WO-\d{3}$")
    quantity: int = Field(gt=0)
    setup_time_minutes: int = Field(gt=0)
    processing_time_minutes: int = Field(gt=0)
    required_capability: str
    priority: Priority
