def test_breakdown(client):
    client.post("/schedule/generate")
    client.post("/simulation/start")
    client.post("/simulation/advance", json={"to_time": "2026-10-03T11:30:00"})
    
    res = client.post("/simulation/breakdown", json={
        "machine_id": "M002",
        "breakdown_time": "2026-10-03T11:30:00"
    })
    assert res.status_code == 200
    assert "WO-002" in res.json()["affected_orders"]
    
    res = client.get("/machines/M002")
    assert res.json()["status"] == "BROKEN_DOWN"
