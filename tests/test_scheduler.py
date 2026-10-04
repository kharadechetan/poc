def test_generate_schedule(client):
    res = client.post("/schedule/generate")
    assert res.status_code == 200
    data = res.json()
    assert len(data["schedule"]) == 10
    assert data["metrics"]["scheduled_orders"] == 10
    
    res = client.get("/schedule")
    assert res.status_code == 200
    
    res2 = client.post("/schedule/generate")
    assert res.json() == res2.json()
