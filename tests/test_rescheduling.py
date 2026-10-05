from datetime import datetime

def test_reschedule(client):
    res = client.post("/schedule/generate")
    data = res.json()
    first_job = sorted([e for e in data["schedule"] if e["machine_id"] == "M002"], key=lambda x: x["setup_start"])[0]
    mid_point = datetime.fromisoformat(first_job["production_start"]) + (datetime.fromisoformat(first_job["production_end"]) - datetime.fromisoformat(first_job["production_start"])) / 2
    
    res = client.post("/simulation/start")
    sim_start = datetime.fromisoformat(res.json()["current_time"])
    
    advance_mins = int((mid_point - sim_start).total_seconds() / 60)
    if advance_mins < 0: advance_mins = 60
        
    client.post("/simulation/advance", json={"minutes": advance_mins})
    client.post("/simulation/breakdown", json={
        "machine_id": "M002",
        "repair_time_minutes": 120
    })
    
    res = client.post("/schedule/reschedule")
    assert res.status_code == 200
    data = res.json()
    assert len(data["affected_work_orders"]) > 0
    
    res = client.get("/schedule/history")
    assert len(res.json()["schedules"]) >= 2
