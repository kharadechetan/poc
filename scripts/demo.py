import httpx
import sys
import json

BASE_URL = "http://127.0.0.1:8000"

def run_demo():
    print("--- 1. Reset and Generate Initial Schedule ---")
    httpx.post(f"{BASE_URL}/admin/reset")
    res = httpx.post(f"{BASE_URL}/schedule/generate")
    if res.status_code != 200:
        print("Failed to generate schedule:", res.text)
        sys.exit(1)
        
    schedule_data = res.json()
    print("Initial schedule generated. Objective:", schedule_data["metrics"]["objective_value"])
    print("Metrics:")
    print(json.dumps(schedule_data["metrics"], indent=2))
    print("\nSchedule:")
    for e in schedule_data["schedule"]:
        print(f"  {e['work_order_id']} on {e['machine_id']}: {e['setup_start']} -> {e['production_end']} (Late: {e['lateness_minutes']}m)")
        
    assert schedule_data["metrics"]["scheduled_orders"] == 10
    
    print("\n--- 2. Start Simulation and Advance to 11:30 ---")
    httpx.post(f"{BASE_URL}/simulation/start")
    httpx.post(f"{BASE_URL}/simulation/advance", json={"to_time": "2026-10-03T11:30:00"})
    
    state = httpx.get(f"{BASE_URL}/simulation/state").json()
    print("State at 11:30:")
    print(json.dumps(state, indent=2))
    
    assert "M002" in state["occupied_machines"], "M002 is not running at 11:30!"
    assert state["running_orders_per_machine"]["M002"] == "WO-002"
    assert "WO-001" in state["completed_orders"]
    
    print("\n--- 3. Breakdown M002 at 11:30 ---")
    res = httpx.post(f"{BASE_URL}/simulation/breakdown", json={
        "machine_id": "M002",
        "breakdown_time": "2026-10-03T11:30:00"
    })
    print("Breakdown response:", res.json())
    
    print("\n--- 4. Affected Orders & Alternatives ---")
    affected = httpx.get(f"{BASE_URL}/simulation/affected-orders").json()
    print("Affected orders:", affected)
    assert "WO-002" in affected
    assert "WO-003" in affected
    assert "WO-004" in affected
    
    alts = httpx.get(f"{BASE_URL}/simulation/alternatives").json()
    print("Alternatives:")
    print(json.dumps(alts, indent=2))
    
    print("\n--- 5. Reschedule ---")
    res = httpx.post(f"{BASE_URL}/schedule/reschedule", timeout=30.0)
    if res.status_code != 200:
        print("Rescheduling failed:", res.text)
        sys.exit(1)
        
    resh = res.json()
    print("Rescheduling successful.")
    print("Changes:")
    for c in resh["changes"]:
        print(f"  {c['work_order_id']}: {c['from_machine']} -> {c['to_machine']}, delay: {c['delay_delta_minutes']} min")
        
    print("\nReasons:")
    for r in resh["reasons"]:
        print(f"  {r['reason']}")
        
    print("\nMetrics Before -> After")
    print(f"  Makespan: {resh['optimization_metrics_before']['makespan_minutes']} -> {resh['optimization_metrics_after']['makespan_minutes']}")
    print(f"  Total Lateness: {resh['optimization_metrics_before']['total_lateness_minutes']} -> {resh['optimization_metrics_after']['total_lateness_minutes']}")
    
    print("\n--- ALL ASSERTIONS PASSED ---")

if __name__ == "__main__":
    run_demo()
