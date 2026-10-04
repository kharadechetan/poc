# AI-Assisted Dynamic Production Scheduler POC

## Overview
This is a FastAPI backend for an AI-Assisted Dynamic Production Scheduler ERP proof of concept. It uses Google OR-Tools (CP-SAT Solver) to dynamically schedule work orders on machines while respecting various constraints (availability, capabilities, release time, delivery dates) and prioritizing urgent orders. It supports simulation, tracking running jobs, and rescheduling around breakdowns.

## Technology Stack
- **Python 3.11**
- **FastAPI**: API framework
- **Google OR-Tools**: CP-SAT solver for schedule optimization
- **SQLite3**: In-process database storing state (machines, work orders, schedules, simulation state, breakdown events)
- **Pydantic**: Data validation and modeling
- **pytest**: Test suite

## Features
- **Deterministic Scheduling**: Generates the exact same schedule given identical state.
- **Multi-Objective Optimization**: Minimizes lateness, late orders, makespan, and completion times in a lexicographic-style weighted sum.
- **Simulation**: Advance time forward, track job states (WAITING, RUNNING, COMPLETED).
- **Dynamic Breakdown**: Break down machines mid-production, identify affected orders, and intelligently reschedule them.
- **Explainability**: Generates plain English explanations for rescheduling decisions.

## Project Structure
```
production_scheduler/
├── app/
│   ├── api/
│   │   ├── routes/          # Routers (machines, scheduling, simulation, work_orders)
│   │   └── deps.py          # Dependencies (DB session)
│   ├── core/
│   │   ├── config.py        # Settings and constants
│   │   ├── errors.py        # Custom exceptions
│   │   └── logging.py       # Logger setup
│   ├── data/
│   │   ├── machines.json    # Seed data
│   │   ├── work_orders.json # Seed data
│   │   └── seed.py          # Database seeding utility
│   ├── db/
│   │   └── database.py      # SQLite connection and schema creation
│   ├── models/
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── alternatives.py  # Alternatives evaluation
│   │   ├── breakdown.py     # Breakdown registration
│   │   ├── explanation.py   # NLP explanation generation
│   │   ├── metrics.py       # Schedule metrics computation
│   │   ├── optimizer.py     # CP-SAT constraint programming logic
│   │   ├── rescheduler.py   # Rescheduling orchestration
│   │   ├── scheduler.py     # Initial schedule orchestration
│   │   ├── simulation.py    # Time simulation tracking
│   │   └── validator.py     # Schedule validation
│   └── main.py              # FastAPI application entry point
├── scripts/
│   └── demo.py              # E2E demo script
├── tests/
│   ├── conftest.py          # Pytest fixtures and DB setup
│   ├── test_api.py          # CRUD API tests
│   ├── test_breakdown.py    # Breakdown API tests
│   ├── test_rescheduling.py # Rescheduling API tests
│   └── test_scheduler.py    # Scheduler API tests
├── requirements.txt
└── README.md
```

## Running the Application
1. **Activate Environment & Install Deps**:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Start the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
3. **Run Demo Script**:
   ```bash
   python scripts\demo.py
   ```
4. **Run Tests**:
   ```bash
   pytest -q
   ```

## Scheduling / Optimization Approach

### Why Constraint Programming (CP-SAT)?
The spec (Section 9) asks the engineer to evaluate multiple approaches. Here is the rationale:

| Approach | Considered? | Verdict |
|----------|------------|---------|
| **Constraint Programming (CP-SAT)** | ✅ Selected | Best fit — natively handles no-overlap, machine-capability, shift-window, and release-time constraints. Produces provably optimal or near-optimal solutions within a time limit. |
| Mixed-Integer Programming (MIP) | Evaluated | Viable but more complex to model disjunctive (no-overlap) scheduling constraints. CP-SAT's `AddNoOverlap` is purpose-built for this. |
| Heuristic / Priority Dispatch | Used for dynamic insertion | Good for real-time single-order insertion (Least Work Remaining heuristic in `heuristic.py`), but cannot globally optimize across all orders simultaneously. |
| Metaheuristic (GA, SA) | Evaluated | Overkill for 10 WOs / 4 machines. No guarantee of feasibility. Better suited for very large instances where CP-SAT hits its time limit. |
| ML-based | Deferred | No historical data exists yet. ML is better suited for *predicting* cycle times or delay probability once real production data is available. The hybrid path is: CP-SAT for scheduling + ML for parameter prediction (future). |

### Model Structure
- **Decision Variables**: For each (work-order, machine, day) triple, an optional interval variable with a boolean presence indicator. Exactly one presence variable is true per work order.
- **Constraints**:
  - `AddNoOverlap` on each machine's interval list (no two jobs overlap).
  - Intervals are bounded within each machine's shift window (`available_from` to `available_to`).
  - Jobs cannot start before their `release_time` or before `current_time` (for rescheduling).
  - Jobs can only be placed on machines whose `capabilities` include the WO's `required_capability`.
  - Machines with active unavailable periods (breakdowns or planned maintenance) have those shifts excluded.
- **Objective** (minimize weighted sum):
  - `1000 × Σ(priority_weight × tardiness)` — meeting delivery dates for urgent orders is the dominant goal.
  - `100 × count(late_orders)` — penalizes each late order.
  - `10 × makespan` — compresses overall schedule length, reducing idle time.
  - `1 × Σ(priority_weight × completion_time)` — earlier completion for high-priority orders.
- **Solver**: Google OR-Tools CP-SAT, 1 worker thread, 10-second time limit, deterministic seed.

### Rescheduling Strategy
When a machine breaks down, the system does **not** rebuild the entire schedule:
1. Jobs already completed or running on healthy machines are **frozen** (fixed intervals).
2. Only affected work orders (on the broken machine) are freed for re-optimization.
3. The solver re-runs with the frozen jobs as hard constraints, finding the best reassignment for affected orders only.

This "fix-and-re-optimize" approach is significantly faster and less disruptive than full rescheduling.

## Assumptions & Design Decisions
1. **Base Date**: The initial scheduling base date is hardcoded to `2026-10-03` to match the data files.
2. **Time Unit**: All solver times are converted to integer minutes relative to the base date.
3. **Priority Weights**: URGENT=10, HIGH=5, MEDIUM=2, LOW=1. The spec mentions "Normal / High / Urgent"; this POC uses `LOW`, `MEDIUM`, `HIGH`, `URGENT` for finer granularity.
4. **Objective Function**: `1000 * Σ(weighted_tardiness) + 100 * (num_late) + 10 * makespan + 1 * Σ(weighted_completion) + 1 * (util_imbalance)`. This ensures that meeting delivery dates for urgent orders takes the absolute highest priority.
5. **No Preemption**: If a machine breaks down while a job is RUNNING, that job loses all progress and is rescheduled from scratch.
6. **Simulation State**: In SQLite, the `current_time` column was renamed to `sim_time` to prevent conflicts with the SQLite built-in `CURRENT_TIME` keyword.
7. **Simulation Time**: The current simulation time is tracked strictly within the `simulation_state` table.
8. **Machine Maintenance**: M003 has a pre-seeded 1-hour planned maintenance window (12:00–13:00 on Oct 13) to demonstrate unavailable-period handling.
9. **Dependencies**: Only built-ins, `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx`, and `ortools` were used. No cloud services or ML.

