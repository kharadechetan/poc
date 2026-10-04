from datetime import datetime
from collections import defaultdict
from app.models.schemas import ScheduleMetrics, Priority
from app.core.config import settings

def compute_metrics(schedule_entries: list, machines: list, all_work_orders: list) -> ScheduleMetrics:
    scheduled_wo_ids = [entry.work_order_id for entry in schedule_entries]
    unscheduled = [wo.id for wo in all_work_orders if wo.id not in scheduled_wo_ids]
    
    total_completion = 0
    makespan = 0
    total_lateness = 0
    late_orders = 0
    weighted_lateness = 0
    
    base_date = datetime.fromisoformat(settings.SIMULATION_START_STR)
    
    if all_work_orders:
        earliest_release = min((wo.release_time for wo in all_work_orders), default=base_date)
    else:
        earliest_release = base_date
        
    machine_busy_minutes = defaultdict(int)
    
    for entry in schedule_entries:
        start = entry.setup_start
        end = entry.production_end
        
        completion_min = int((end - earliest_release).total_seconds() / 60)
        total_completion += completion_min
        makespan = max(makespan, completion_min)
        
        priority_weight = settings.get_priority_weight(entry.priority)
        
        lateness = getattr(entry, "lateness_minutes", 0)
        if lateness > 0:
            total_lateness += lateness
            late_orders += 1
            weighted_lateness += priority_weight * lateness
            
        dur = entry.setup_duration_minutes + entry.processing_duration_minutes
        machine_busy_minutes[entry.machine_id] += dur

    machine_utilization = {}
    total_available_minutes = 0
    total_busy_minutes = sum(machine_busy_minutes.values())
    
    horizon_days = max(1, (makespan // (24 * 60)) + 1)
    
    for m in machines:
        avail_start_str = str(m.available_from)
        avail_end_str = str(m.available_to)
        
        start_time = datetime.strptime(avail_start_str[:5], "%H:%M")
        end_time = datetime.strptime(avail_end_str[:5], "%H:%M")
        
        shift_len = int((end_time - start_time).total_seconds() / 60)
        if shift_len < 0: shift_len += 24*60
        
        avail_mins = shift_len * horizon_days
        total_available_minutes += avail_mins
        
        busy = machine_busy_minutes.get(m.id, 0)
        util = (busy / avail_mins * 100) if avail_mins > 0 else 0
        machine_utilization[m.id] = round(util, 2)
        
    overall_util = (total_busy_minutes / total_available_minutes * 100) if total_available_minutes > 0 else 0
    
    weighted_completion = sum(
        settings.get_priority_weight(entry.priority) * int((entry.production_end - earliest_release).total_seconds() / 60)
        for entry in schedule_entries
    )
    
    if machine_busy_minutes:
        max_load = max(machine_busy_minutes.values())
        min_load = min([machine_busy_minutes.get(m.id, 0) for m in machines])
        imbalance = max_load - min_load
    else:
        imbalance = 0
        
    objective = (
        settings.COEFF_WEIGHTED_TARDINESS * weighted_lateness +
        settings.COEFF_LATE_ORDERS * late_orders +
        settings.COEFF_MAKESPAN * makespan +
        settings.COEFF_COMPLETION_TIME * weighted_completion + 
        settings.COEFF_UTILIZATION_IMBALANCE * imbalance
    )
    
    return ScheduleMetrics(
        scheduled_orders=len(scheduled_wo_ids),
        unscheduled_orders=unscheduled,
        total_completion_time_minutes=total_completion,
        makespan_minutes=makespan,
        total_lateness_minutes=total_lateness,
        number_of_late_orders=late_orders,
        weighted_lateness=weighted_lateness,
        machine_utilization=machine_utilization,
        overall_machine_utilization=round(overall_util, 2),
        objective_value=objective
    )
