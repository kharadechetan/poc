import httpx
import sys
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def run_demo():
    print("=" * 60)
    print("  AI-Assisted Dynamic Production Scheduler — E2E Demo")
    print("=" * 60)

    # ── 1. Reset ──
    print("\n--- 1. Reset Database ---")
    httpx.post(f"{BASE_URL}/admin/reset")
    print("Database reset and seeded.")

    # ── 2. Generate Initial Schedule ──
    print("\n--- 2. Generate Initial Schedule ---")
    res = httpx.post(f"{BASE_URL}/schedule/generate")
    if res.status_code != 200:
        print("FAILED:", res.text)
        sys.exit(1)
    data = res.json()
    print(f"Solver scheduled {data['metrics']['scheduled_orders']} orders.")
    print(f"Objective value: {data['metrics']['objective_value']}")
    print(f"Makespan: {data['metrics']['makespan_minutes']} min")
    print(f"Late orders: {data['metrics']['number_of_late_orders']}")
    print("\nInitial Schedule:")
    print(f"  {'WO':<8} {'Machine':<8} {'Start':>22} {'End':>22} {'Late':>6}")
    for e in sorted(data["schedule"], key=lambda x: x["setup_start"]):
        print(f"  {e['work_order_id']:<8} {e['machine_id']:<8} {e['setup_start']:>22} {e['production_end']:>22} {e['lateness_minutes']:>5}m")

    assert data["metrics"]["scheduled_orders"] == 10, "Not all 10 WOs scheduled!"

    # Find a machine with multiple jobs for the demo breakdown
    # Identify when M002 has a job running
    m002_jobs = [e for e in data["schedule"] if e["machine_id"] == "M002"]
    if not m002_jobs:
        print("WARNING: No jobs on M002 — picking first machine with jobs for breakdown demo")
        target_machine = data["schedule"][0]["machine_id"]
        target_jobs = [e for e in data["schedule"] if e["machine_id"] == target_machine]
    else:
        target_machine = "M002"
        target_jobs = m002_jobs

    # Pick a time in the middle of the first job on the target machine
    first_job = sorted(target_jobs, key=lambda x: x["setup_start"])[0]
    job_start = datetime.fromisoformat(first_job["production_start"])
    job_end = datetime.fromisoformat(first_job["production_end"])
    # Mid-point of the first production run
    mid_point = job_start + (job_end - job_start) / 2

    # ── 3. Start Simulation and Advance ──
    print(f"\n--- 3. Start Simulation & Advance to {mid_point.isoformat()} ---")
    res = httpx.post(f"{BASE_URL}/simulation/start")
    sim_start = datetime.fromisoformat(res.json()["current_time"])
    print(f"Simulation started at {sim_start.isoformat()}")

    advance_mins = int((mid_point - sim_start).total_seconds() / 60)
    if advance_mins <= 0:
        print(f"WARNING: mid_point {mid_point} is in the past relative to sim start {sim_start}")
        advance_mins = 60
    res = httpx.post(f"{BASE_URL}/simulation/advance", json={"minutes": advance_mins})
    print(f"Advanced {advance_mins} minutes → {res.json()['current_time']}")

    state = httpx.get(f"{BASE_URL}/simulation/state").json()
    print(f"Running jobs: {[k + '=' + (v or '-') for k, v in state['running_orders_per_machine'].items() if v]}")
    print(f"Completed: {state['completed_orders']}")

    # ── 4. Machine Breakdown ──
    print(f"\n--- 4. Simulate Breakdown of {target_machine} ---")
    res = httpx.post(f"{BASE_URL}/simulation/breakdown", json={
        "machine_id": target_machine,
        "repair_time_minutes": 120
    })
    if res.status_code != 200:
        print("Breakdown failed:", res.text)
        sys.exit(1)
    bd = res.json()
    print(f"Breakdown event #{bd['event_id']}")
    print(f"Affected orders: {bd['affected_orders']}")

    # ── 5. Identify Affected Orders & Alternatives ──
    print("\n--- 5. Affected Orders & Alternative Machines ---")
    affected = httpx.get(f"{BASE_URL}/simulation/affected-orders").json()
    print(f"Affected: {affected}")
    assert len(affected) > 0, "No affected orders detected!"

    alts = httpx.get(f"{BASE_URL}/simulation/alternatives").json()
    for wo_id, candidates in alts.items():
        feasible = [c for c in candidates if c["feasible"]]
        infeasible = [c for c in candidates if not c["feasible"]]
        print(f"  {wo_id}: {len(feasible)} feasible, {len(infeasible)} rejected")

    # ── 6. Reschedule ──
    print("\n--- 6. AI Rescheduling ---")
    res = httpx.post(f"{BASE_URL}/schedule/reschedule", timeout=30.0)
    if res.status_code != 200:
        print("Rescheduling FAILED:", res.text)
        sys.exit(1)
    resh = res.json()
    print("Rescheduling successful.\n")

    print(f"  {'WO':<8} {'From':>6} {'To':>6} {'Old Start':>22} {'New Start':>22} {'Delay':>7}")
    print("  " + "-" * 75)
    for c in resh["changes"]:
        print(f"  {c['work_order_id']:<8} {c['from_machine']:>6} {c['to_machine']:>6} "
              f"{c['old_start']:>22} {c['new_start']:>22} {c['delay_delta_minutes']:>+6}m")

    print("\nReasons:")
    for r in resh["reasons"]:
        print(f"  → {r['reason']}")

    print("\nMetrics Comparison:")
    mb = resh["optimization_metrics_before"]
    ma = resh["optimization_metrics_after"]
    print(f"  Makespan:       {mb['makespan_minutes']:>6} → {ma['makespan_minutes']:>6} min")
    print(f"  Total Lateness: {mb['total_lateness_minutes']:>6} → {ma['total_lateness_minutes']:>6} min")
    print(f"  Late Orders:    {mb['number_of_late_orders']:>6} → {ma['number_of_late_orders']:>6}")
    print(f"  Utilization:    {mb['overall_machine_utilization']:>5.1f}% → {ma['overall_machine_utilization']:>5.1f}%")

    # ── 7. Schedule History ──
    print("\n--- 7. Schedule Version History ---")
    hist = httpx.get(f"{BASE_URL}/schedule/history").json()
    print(f"Total schedule versions: {len(hist['schedules'])}")
    print(f"Rescheduling events: {len(hist['rescheduling_events'])}")

    print("\n" + "=" * 60)
    print("  ALL CHECKS PASSED — POC Demo Complete")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
