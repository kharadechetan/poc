import os
import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = "test_scheduler.db"

from app.main import app
from app.db.database import init_db, reset_db
from app.data.seed import seed_database

@pytest.fixture(autouse=True)
def setup_db():
    reset_db()
    seed_database()
    yield

@pytest.fixture
def client():
    return TestClient(app)
