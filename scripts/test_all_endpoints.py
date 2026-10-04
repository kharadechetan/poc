import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_all():
    print("Testing 19 Endpoints...")
    
    def check(method, url, data=None):
        req_url = BASE_URL + url
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(data).encode('utf-8') if data else None
        
        req = urllib.request.Request(req_url, data=body, headers=headers if body else {}, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                print(f"OK: {method} {url}")
        except urllib.error.HTTPError as e:
            print(f"FAILED: {method} {url} - {e.code} {e.reason}")
            try:
                print(e.read().decode())
            except:
                pass
        except Exception as e:
            print(f"FAILED: {method} {url} - {str(e)}")

    # 1. /health
    check("GET", "/health")
    
    # 2. /admin/reset
    check("POST", "/admin/reset")
    
    # 3. /machines
    check("GET", "/machines")
    
    # 4. /machines/{id}
    check("GET", "/machines/M001")
    
    # 5. /machines (POST)
    check("POST", "/machines", data={
        "id": "M005", "name": "Test Machine", "capabilities": ["milling"], 
        "status": "AVAILABLE", "available_from": "08:00", "available_to": "18:00"
    })
    check("GET", "/machines/M005")
    
    # 6. /work-orders
    check("GET", "/work-orders")
    
    # 7. /work-orders/{id}
    check("GET", "/work-orders/WO-001")
    
    # 8. /work-orders (POST)
    check("POST", "/work-orders", data={
        "id": "WO-999", "name": "Test", "priority": "HIGH", "required_capability": "milling",
        "quantity": 100,
        "setup_time_minutes": 10, "processing_time_minutes": 60
    })
    check("GET", "/work-orders/WO-999")
    
    # 9. /schedule/generate
    check("POST", "/schedule/generate")
    
    # 10. /schedule
    check("GET", "/schedule")
    
    # 11. /schedule/metrics
    check("GET", "/schedule/metrics")
    
    # 12. /schedule/history
    check("GET", "/schedule/history")
    
    # 13. /simulation/start
    check("POST", "/simulation/start")
    
    # 14. /simulation/state
    check("GET", "/simulation/state")
    
    # 15. /simulation/advance
    check("POST", "/simulation/advance", data={"minutes": 30})
    
    # 16. /simulation/breakdown
    check("POST", "/simulation/breakdown", data={
        "machine_id": "M001", "repair_time_minutes": 120
    })
    
    # 17. /simulation/affected-orders
    check("GET", "/simulation/affected-orders")
    
    # 18. /simulation/alternatives
    check("GET", "/simulation/alternatives")
    
    # 19. /schedule/reschedule
    check("POST", "/schedule/reschedule")
    
    # 20. /work-orders (POST a new unscheduled one)
    check("POST", "/work-orders", data={
        "id": "WO-888", "name": "Dynamic Order", "priority": "HIGH", "required_capability": "drilling",
        "quantity": 100,
        "setup_time_minutes": 10, "processing_time_minutes": 60
    })
    
    # 21. /schedule/insert-dynamic
    check("POST", "/schedule/insert-dynamic/WO-888")

if __name__ == "__main__":
    test_all()
