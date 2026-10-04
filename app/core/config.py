import os
from datetime import datetime

class Settings:
    PROJECT_NAME: str = "AI-Assisted Dynamic Production Scheduler"
    
    # Time handling base
    BASE_DATE_STR: str = "2026-10-03"
    SIMULATION_START_STR: str = "2026-10-03T08:00:00"
    
    # SQLite
    DB_PATH: str = os.getenv("DB_PATH", "scheduler.db")
    
    # Solver Config
    NUM_SEARCH_WORKERS: int = 1
    RANDOM_SEED: int = 42
    MAX_TIME_IN_SECONDS: float = 10.0
    
    # Objective weights
    WEIGHT_URGENT: int = 10
    WEIGHT_HIGH: int = 5
    WEIGHT_MEDIUM: int = 2
    WEIGHT_LOW: int = 1
    
    COEFF_WEIGHTED_TARDINESS: int = 1000
    COEFF_LATE_ORDERS: int = 100
    COEFF_MAKESPAN: int = 10
    COEFF_COMPLETION_TIME: int = 1
    COEFF_UTILIZATION_IMBALANCE: int = 1

    @classmethod
    def get_priority_weight(cls, priority: str) -> int:
        mapping = {
            "URGENT": cls.WEIGHT_URGENT,
            "HIGH": cls.WEIGHT_HIGH,
            "MEDIUM": cls.WEIGHT_MEDIUM,
            "LOW": cls.WEIGHT_LOW
        }
        return mapping.get(priority, cls.WEIGHT_LOW)
    
settings = Settings()
