import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
from app.models.schemas import Machine, WorkOrder, ScheduleEntry, ScheduleStatus
from app.core.config import settings
from app.core.logging import logger

def solve_schedule(
    machines: List[Machine], 
    work_orders: List[WorkOrder], 
    fixed_jobs: List[ScheduleEntry] = None,
    current_time: datetime = None
) -> Tuple[List[ScheduleEntry], str, float, bool]:
    
    start_wall_time = time.time()
    
    if fixed_jobs is None: fixed_jobs = []
    base_date = datetime.fromisoformat(settings.SIMULATION_START_STR)
    if current_time is None: current_time = base_date
    
    model = cp_model.CpModel()
    
    fixed_wo_ids = {job.work_order_id for job in fixed_jobs}
    wos_to_schedule = [wo for wo in work_orders if wo.id not in fixed_wo_ids]
    
    earliest_release = min((wo.release_time for wo in work_orders), default=base_date)
    horizon_start = min(earliest_release, current_time).replace(second=0, microsecond=0)
    horizon_days = 30
    horizon_mins = horizon_days * 24 * 60
    
    def dt_to_min(dt: datetime) -> int:
        return int((dt - horizon_start).total_seconds() / 60)
        
    def min_to_dt(m: int) -> datetime:
        return horizon_start + timedelta(minutes=m)

    # Machine data
    machine_dict = {m.id: m for m in machines}
    machine_capacity = {m.id: [] for m in machines}
    
    # Setup fixed jobs
    for fjob in fixed_jobs:
        s = dt_to_min(fjob.setup_start)
        e = dt_to_min(fjob.production_end)
        interval = model.NewIntervalVar(s, e - s, e, f'fixed_{fjob.work_order_id}')
        machine_capacity[fjob.machine_id].append(interval)
        
    # Variables for jobs to schedule
    job_vars = {}
    
    for wo in wos_to_schedule:
        dur = wo.setup_time_minutes + wo.processing_time_minutes
        
        # Valid machines
        compatible_machines = [m for m in machines if wo.required_capability in m.capabilities]
        
        if not compatible_machines:
            # Cannot schedule
            continue
            
        machine_vars = []
        
        for m in compatible_machines:
            # Job must fit in a single shift. We create optional variables for each day.
            for d in range(horizon_days):
                day_date = horizon_start.date() + timedelta(days=d)
                
                shift_start_dt = datetime.combine(day_date, datetime.strptime(str(m.available_from)[:5], "%H:%M").time())
                shift_end_dt = datetime.combine(day_date, datetime.strptime(str(m.available_to)[:5], "%H:%M").time())
                
                s_min = dt_to_min(shift_start_dt)
                e_min = dt_to_min(shift_end_dt)
                
                if m.status in ["UNAVAILABLE", "BROKEN_DOWN"] and m.unavailable_from:
                    blocked_s = dt_to_min(m.unavailable_from)
                    blocked_e = dt_to_min(m.unavailable_until) if m.unavailable_until else horizon_mins
                    
                    if s_min < blocked_e and e_min > blocked_s:
                        # For simplicity, if shift overlaps blocked interval, we just don't schedule in this shift.
                        # (Strictly speaking, we could schedule before or after within the shift, but this is simpler and safer)
                        continue
                
                earliest_start = max(s_min, dt_to_min(wo.release_time), dt_to_min(current_time))
                latest_end = e_min
                
                if latest_end - earliest_start >= dur:
                    is_present = model.NewBoolVar(f'pres_{wo.id}_{m.id}_day{d}')
                    start_var = model.NewIntVar(earliest_start, latest_end - dur, f'start_{wo.id}_{m.id}_day{d}')
                    end_var = model.NewIntVar(earliest_start + dur, latest_end, f'end_{wo.id}_{m.id}_day{d}')
                    
                    interval = model.NewOptionalIntervalVar(start_var, dur, end_var, is_present, f'int_{wo.id}_{m.id}_day{d}')
                    machine_capacity[m.id].append(interval)
                    
                    machine_vars.append({
                        'is_present': is_present,
                        'start': start_var,
                        'end': end_var,
                        'm_id': m.id
                    })
        
        if machine_vars:
            # Exactly one shift/machine selected
            model.AddExactlyOne([v['is_present'] for v in machine_vars])
            
            # Global start/end for objective
            job_start = model.NewIntVar(0, horizon_mins, f'start_{wo.id}')
            job_end = model.NewIntVar(0, horizon_mins, f'end_{wo.id}')
            
            for v in machine_vars:
                model.Add(job_start == v['start']).OnlyEnforceIf(v['is_present'])
                model.Add(job_end == v['end']).OnlyEnforceIf(v['is_present'])
                
            job_vars[wo.id] = {
                'start': job_start,
                'end': job_end,
                'machine_vars': machine_vars,
                'wo': wo
            }
        else:
            # Infeasible to schedule this WO
            pass
            
    # No overlap on machines
    for m_id, intervals in machine_capacity.items():
        if intervals:
            model.AddNoOverlap(intervals)
            
    # Objective
    makespan_var = model.NewIntVar(0, horizon_mins, 'makespan')
    all_ends = [v['end'] for v in job_vars.values()]
    if all_ends:
        model.AddMaxEquality(makespan_var, all_ends)
    else:
        model.Add(makespan_var == 0)
        
    objective_terms = []
    objective_terms.append(settings.COEFF_MAKESPAN * makespan_var)
    
    for wo_id, jv in job_vars.items():
        wo = jv['wo']
        weight = settings.get_priority_weight(wo.priority)
        
        due_dt = datetime.combine(wo.delivery_date, datetime.strptime("17:00", "%H:%M").time())
        due_min = dt_to_min(due_dt)
        
        # Lateness
        lateness = model.NewIntVar(0, horizon_mins, f'late_{wo_id}')
        # lateness >= end - due_min
        model.Add(lateness >= jv['end'] - due_min)
        # lateness >= 0
        
        is_late = model.NewBoolVar(f'is_late_{wo_id}')
        model.Add(lateness > 0).OnlyEnforceIf(is_late)
        model.Add(lateness == 0).OnlyEnforceIf(is_late.Not())
        
        objective_terms.append(settings.COEFF_WEIGHTED_TARDINESS * weight * lateness)
        objective_terms.append(settings.COEFF_LATE_ORDERS * is_late)
        objective_terms.append(settings.COEFF_COMPLETION_TIME * weight * jv['end'])
        
    model.Minimize(sum(objective_terms))
    
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = settings.NUM_SEARCH_WORKERS
    solver.parameters.random_seed = settings.RANDOM_SEED
    solver.parameters.max_time_in_seconds = settings.MAX_TIME_IN_SECONDS
    
    status = solver.Solve(model)
    wall_time = time.time() - start_wall_time
    
    final_schedule = list(fixed_jobs)
    
    status_str = solver.StatusName(status)
    proven_optimal = (status == cp_model.OPTIMAL)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for wo_id, jv in job_vars.items():
            wo = jv['wo']
            for v in jv['machine_vars']:
                if solver.Value(v['is_present']):
                    s_min = solver.Value(v['start'])
                    s_dt = min_to_dt(s_min)
                    p_start = s_dt + timedelta(minutes=wo.setup_time_minutes)
                    p_end = p_start + timedelta(minutes=wo.processing_time_minutes)
                    
                    due_dt = datetime.combine(wo.delivery_date, datetime.strptime("17:00", "%H:%M").time())
                    late = max(0, int((p_end - due_dt).total_seconds() / 60))
                    
                    entry = ScheduleEntry(
                        work_order_id=wo.id,
                        machine_id=v['m_id'],
                        setup_start=s_dt,
                        production_start=p_start,
                        production_end=p_end,
                        setup_duration_minutes=wo.setup_time_minutes,
                        processing_duration_minutes=wo.processing_time_minutes,
                        priority=wo.priority,
                        delivery_date=wo.delivery_date,
                        status=ScheduleStatus.WAITING,
                        lateness_minutes=late
                    )
                    final_schedule.append(entry)
                    break
                    
    return final_schedule, status_str, wall_time, proven_optimal
