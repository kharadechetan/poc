def test_reschedule(client):
    client.post("/schedule/generate")
    client.post("/simulation/start")
    client.post("/simulation/advance", json={"to_time": "2026-10-03T11:30:00"})
    client.post("/simulation/breakdown", json={
        "machine_id": "M002",
        "breakdown_time": "2026-10-03T11:30:00"
    })
    
    res = client.post("/schedule/reschedule")
    assert res.status_code == 200
    data = res.json()
    assert "WO-002" in data["affected_work_orders"]
    
    res = client.get("/schedule/history")
    assert len(res.json()["schedules"]) == 2
