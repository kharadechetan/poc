def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_machines_crud(client):
    res = client.get("/machines")
    assert res.status_code == 200
    assert len(res.json()) == 4
    
    res = client.post("/machines", json={})
    assert res.status_code == 422
    
    res = client.post("/machines", json={
        "id": "M005", "name": "Test", "capabilities": ["welding"],
        "available_from": "08:00", "available_to": "16:00", "status": "AVAILABLE"
    })
    assert res.status_code == 200
    assert res.json()["id"] == "M005"
    
    res = client.post("/machines", json={
        "id": "M005", "name": "Test2", "capabilities": ["welding"],
        "available_from": "08:00", "available_to": "16:00", "status": "AVAILABLE"
    })
    assert res.status_code == 409

def test_work_orders_crud(client):
    res = client.get("/work-orders")
    assert res.status_code == 200
    assert len(res.json()) == 10
    
    res = client.post("/work-orders", json={
        "id": "WO-999", "quantity": 1, "setup_time_minutes": 10, "processing_time_minutes": 10,
        "required_capability": "magic", "release_time": "2026-10-03T08:00:00",
        "delivery_date": "2026-10-03", "priority": "LOW"
    })
    assert res.status_code == 422
