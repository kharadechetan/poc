from typing import Iterator
import sqlite3
from app.db.database import get_db

def get_db_session() -> Iterator[sqlite3.Connection]:
    yield from get_db()
