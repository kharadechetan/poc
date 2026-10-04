from datetime import datetime
from app.models.schemas import Reason

def generate_rescheduling_reason(
    wo_id: str, 
    old_m: str, 
    new_m: str, 
    breakdown_time: datetime, 
    capability: str, 
    old_start: datetime,
    old_end: datetime,
    new_start: datetime,
    new_end: datetime,
    old_late: int,
    new_late: int,
    priority: str,
    was_interrupted: bool,
    alternatives: list
) -> Reason:
    
    text = f"Work Order {wo_id} (Priority: {priority}) required {capability}."
    
    if was_interrupted:
        text += f" It was interrupted on {old_m} at {breakdown_time.isoformat()} (progress lost, restarting)."
    else:
        text += f" Its scheduled machine {old_m} broke down at {breakdown_time.isoformat()} before it could start."
        
    if old_m == new_m:
        text += f" It remains on {new_m} but shifted from {old_start.isoformat()} to {new_start.isoformat()}."
    else:
        text += f" It was moved from {old_m} to {new_m}."
        
    num_examined = len(alternatives)
    num_rejected = sum(1 for a in alternatives if not a.get("feasible"))
    text += f" Evaluated {num_examined} candidates ({num_rejected} infeasible/broken)."
    
    text += f" New completion time is {new_end.isoformat()} (was {old_end.isoformat()})."
    
    if new_late > old_late:
        text += f" Lateness increased from {old_late} to {new_late} mins."
    elif new_late < old_late:
        text += f" Lateness decreased from {old_late} to {new_late} mins."
    else:
        text += f" Lateness unchanged ({new_late} mins)."
        
    return Reason(work_order_id=wo_id, reason=text)
