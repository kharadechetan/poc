from datetime import datetime, timedelta
from typing import List
from app.models.schemas import Machine, WorkOrder, ScheduleEntry

class ScheduleValidationError(Exception):
    pass

def validate_schedule(entries: List[ScheduleEntry], machines: List[Machine], work_orders: List[WorkOrder]):
    machine_dict = {m.id: m for m in machines}
    wo_dict = {wo.id: wo for wo in work_orders}
    
    machine_entries = {}
    for e in entries:
        if e.machine_id not in machine_entries:
            machine_entries[e.machine_id] = []
        machine_entries[e.machine_id].append(e)
        
    for m_id, m_entries in machine_entries.items():
        if m_id not in machine_dict:
            raise ScheduleValidationError(f"Unknown machine {m_id}")
            
        m = machine_dict[m_id]
        m_entries.sort(key=lambda x: x.setup_start)
        
        prev_end = None
        for e in m_entries:
            wo = wo_dict.get(e.work_order_id)
            if not wo:
                raise ScheduleValidationError(f"Unknown work order {e.work_order_id}")
            
            if wo.required_capability not in m.capabilities:
                raise ScheduleValidationError(f"WO {wo.id} requires {wo.required_capability} but machine {m.id} doesn't support it")
                
            if e.setup_duration_minutes != wo.setup_time_minutes:
                raise ScheduleValidationError(f"WO {wo.id} setup duration mismatch")
            if e.processing_duration_minutes != wo.processing_time_minutes:
                raise ScheduleValidationError(f"WO {wo.id} processing duration mismatch")
                
            expected_prod_start = e.setup_start + timedelta(minutes=e.setup_duration_minutes)
            if e.production_start != expected_prod_start:
                raise ScheduleValidationError(f"WO {wo.id} production_start != setup_start + setup_duration")
                
            expected_prod_end = e.production_start + timedelta(minutes=e.processing_duration_minutes)
            if e.production_end != expected_prod_end:
                raise ScheduleValidationError(f"WO {wo.id} production_end != production_start + processing_duration")
                
            if e.setup_start < wo.release_time:
                raise ScheduleValidationError(f"WO {wo.id} starts before release time. setup_start: {e.setup_start}, release_time: {wo.release_time}")
                
            if prev_end and e.setup_start < prev_end:
                raise ScheduleValidationError(f"Overlap on machine {m.id}: {e.work_order_id} starts before previous job ends")
            prev_end = e.production_end
            
            start_date = e.setup_start.date()
            end_date = e.production_end.date()
            
            shift_start_time = datetime.strptime(str(m.available_from)[:5], "%H:%M").time()
            shift_end_time = datetime.strptime(str(m.available_to)[:5], "%H:%M").time()
            
            if start_date != end_date:
                raise ScheduleValidationError(f"WO {wo.id} crosses midnight, violates single-day window rule")
                
            if e.setup_start.time() < shift_start_time or e.production_end.time() > shift_end_time:
                raise ScheduleValidationError(f"WO {wo.id} is outside shift window {m.available_from}-{m.available_to}")
                
            if m.status in ["UNAVAILABLE", "BROKEN_DOWN"] and m.unavailable_from:
                blocked_start = m.unavailable_from
                blocked_end = m.unavailable_until if m.unavailable_until else datetime.max.replace(tzinfo=None)
                
                if e.setup_start < blocked_end and e.production_end > blocked_start:
                    raise ScheduleValidationError(f"WO {wo.id} overlaps with blocked interval on {m.id}")
