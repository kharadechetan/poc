# AI-Assisted Dynamic Production Scheduler - API Walkthrough

This document serves as a comprehensive guide to the **21** available API endpoints in the system. It explains what each endpoint does, the input it requires, and what it returns.

You can interact with all these endpoints directly at **http://127.0.0.1:8000/docs** (Swagger UI).

*Note: Dates and times can be passed using commas (e.g. `10,08,2026 14,30`) or standard ISO formats.*

---

## Recommended Execution Flow (How to Demo the System)

If you are demonstrating this Proof of Concept, follow these exact endpoints in order:

1. **`POST /admin/reset`** – Start with a completely clean slate.
2. **`POST /schedule/generate`** – Tell the AI to generate the initial, mathematically perfect schedule.
3. **`POST /simulation/start`** – Turn on the factory clock.
4. **`GET /simulation/state`** – Look at the active factory floor.
5. **`POST /simulation/advance`** – Fast-forward time to `03,10,2026 11,30`.
6. **`POST /simulation/breakdown`** – Simulate `M002` breaking down at `11,30`.
7. **`POST /schedule/reschedule`** – Watch the AI automatically rescue and move the interrupted jobs.
8. **`POST /work-orders`** – (Optional) Create a brand new urgent work order.
9. **`POST /schedule/insert-dynamic/{work_order_id}`** – (Optional) Watch the Load-Balancer heuristic safely slot the new order into the running factory.

---

## 1. System & Admin

### `GET /health`
* **What it does:** Checks if the API server is up and running.
* **Input:** None.
* **Returns:** `{"status": "ok"}`

### `POST /admin/reset`
* **What it does:** Wipes the entire SQLite database and re-seeds it with default dummy data (`machines.json` and `work_orders.json`). Use this to completely reset your simulation state.
* **Input:** None.
* **Returns:** `{"message": "Database reset and seeded."}`

---

## 2. Master Data (Machines & Work Orders)

### `GET /machines`
* **What it does:** Fetches the list of all available machines on the factory floor.
* **Input:** None.
* **Returns:** A list of machine objects containing ID, name, capabilities, status, and shift availability.

### `GET /machines/{machine_id}`
* **What it does:** Fetches the specific details of a single machine.
* **Input:** Path parameter `machine_id` (e.g., `M001`).
* **Returns:** A single machine object.

### `POST /machines`
* **What it does:** Adds a brand new machine to the factory floor.
* **Input:** 
  ```json
  {
    "id": "M005",
    "name": "New Lathe",
    "capabilities": ["turning"],
    "status": "AVAILABLE",
    "available_from": "08,00",
    "available_to": "18,00"
  }
  ```
* **Returns:** The created machine object.

### `GET /work-orders`
* **What it does:** Fetches the list of all work orders currently existing in the database.
* **Input:** None.
* **Returns:** A list of work order objects.

### `GET /work-orders/{work_order_id}`
* **What it does:** Fetches the specific details of a single work order.
* **Input:** Path parameter `work_order_id` (e.g., `WO-001`).
* **Returns:** A single work order object.

### `POST /work-orders`
* **What it does:** Injects a brand new work order into the system.
* **Input:** 
  ```json
  {
    "id": "WO-999",
    "name": "Urgent Part",
    "priority": "HIGH",
    "required_capability": "drilling",
    "quantity": 100,
    "release_time": "03,10,2026 08,00",
    "setup_time_minutes": 10,
    "processing_time_minutes": 60,
    "delivery_date": "04,10,2026"
  }
  ```
* **Returns:** The created work order object.

---

## 3. Core AI Scheduling

### `POST /schedule/generate`
* **What it does:** Triggers the AI Solver (Google OR-Tools CP-SAT) to analyze all pending work orders and available machines, and calculate the most mathematically optimal schedule.
* **Input:** None.
* **Returns:** The full generated schedule (list of `ScheduleEntry` objects) along with optimization metrics.

### `GET /schedule`
* **What it does:** Retrieves the active, currently executing schedule version from the database.
* **Input:** None.
* **Returns:** The active schedule and its metrics.

### `GET /schedule/machine-work-orders`
* **What it does:** Organizes the active schedule by machine, providing a quick lookup of which work orders are assigned to which machines in sequential order.
* **Input:** None.
* **Returns:** A dictionary mapping each `machine_id` to its ordered list of `work_order_id`s.

### `GET /schedule/metrics`
* **What it does:** Evaluates the active schedule and returns key performance indicators.
* **Input:** None.
* **Returns:** JSON containing Makespan, Total Lateness, and Machine Utilization percentages.

### `GET /schedule/history`
* **What it does:** Retrieves all past versions of schedules and the log of all rescheduling events.
* **Input:** None.
* **Returns:** A history list of schedule versions and a history of rescheduling/breakdown events.

### `POST /schedule/reschedule`
* **What it does:** The AI Rescue! Freezes completed/unaffected jobs, removes the broken machine from the pool, and mathematically recalculates the best recovery paths for the affected orders.
* **Input:** None.
* **Returns:** The brand new revised schedule, updated metrics, and **Plain English reasons** explaining exactly how and why the AI rescued each job (e.g. "Moved from M002 to M004").

### `POST /schedule/insert-dynamic/{work_order_id}`
* **What it does:** Dynamic Order Insertion using the **Least Work Remaining** heuristic. Safely injects a newly created work order into the running factory without breaking existing jobs. It automatically finds the compatible machine with the shortest queue and assigns it.
* **Input:** Path parameter `work_order_id` (e.g., `WO-999`).
* **Returns:** A success message, the newly created schedule entry, and the heuristic rationale for why it picked that specific machine.

---

## 4. Simulation Engine

### `POST /simulation/start`
* **What it does:** Turns on the simulation clock. Must be called before `advance` or `state` can be used.
* **Input:** (Optional) 
  ```json
  { "start_time": "03,10,2026 08,00" }
  ```
* **Returns:** Success message and the `current_time`.

### `GET /simulation/state`
* **What it does:** Returns a real-time dashboard of the factory exactly at the current simulated time.
* **Input:** None.
* **Returns:** Lists of jobs that are currently `COMPLETED`, `RUNNING`, and `WAITING`.

### `POST /simulation/advance`
* **What it does:** Fast-forwards the factory clock. As time advances, jobs transition logically from `WAITING` to `RUNNING` to `COMPLETED` based on the active schedule.
* **Input:** Either `minutes` OR `to_time`:
  ```json
  { "to_time": "03,10,2026 11,30" }
  ```
* **Returns:** Success message and the updated `current_time`.

### `POST /simulation/breakdown`
* **What it does:** Simulates a catastrophic machine failure at a specific point in time, interrupting any job currently running on it.
* **Input:**
  ```json
  {
    "machine_id": "M002",
    "breakdown_time": "03,10,2026 11,30",
    "repair_time_minutes": 120
  }
  ```
* **Returns:** The Breakdown Event ID and a list of `affected_orders`.

### `GET /simulation/affected-orders`
* **What it does:** Lists which Work Orders were interrupted or are now stuck waiting for the broken machine.
* **Input:** None.
* **Returns:** A list of `work_order_id`s.

### `GET /simulation/alternatives`
* **What it does:** The AI analyzes all affected jobs and scans the factory for alternative healthy machines, outputting exact reasons for acceptance or rejection.
* **Input:** None.
* **Returns:** JSON explaining feasible and infeasible alternative machines for every affected order.
