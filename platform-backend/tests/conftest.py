import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine
from sqlalchemy import text


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_connection():
    with engine.connect() as conn:
        yield conn


def check_table_exists(conn, table_name: str) -> bool:
    query = text(
        "SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_schema='public' AND table_name=:name)"
    )
    result = conn.execute(query, {"name": table_name}).scalar()
    return bool(result)