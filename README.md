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

## Assumptions & Design Decisions
1. **Base Date**: The initial scheduling base date is hardcoded to `2026-10-03` to match the data files.
2. **Time Unit**: All solver times are converted to integer minutes relative to the base date.
3. **Priority Weights**: URGENT=10, HIGH=5, MEDIUM=2, LOW=1.
4. **Objective Function**: `1000 * Σ(weighted_tardiness) + 100 * (num_late) + 10 * makespan + 1 * Σ(weighted_completion) + 1 * (util_imbalance)`. This ensures that meeting delivery dates for urgent orders takes the absolute highest priority.
5. **No Preemption**: If a machine breaks down while a job is RUNNING, that job loses all progress and is rescheduled from scratch.
6. **Simulation State**: In SQLite, the `current_time` column was renamed to `sim_time` to prevent conflicts with the SQLite built-in `CURRENT_TIME` keyword.
7. **Simulation Time**: The current simulation time is tracked strictly within the `simulation_state` table.
8. **Dependencies**: Only built-ins, `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx`, and `ortools` were used. No cloud services or ML.
