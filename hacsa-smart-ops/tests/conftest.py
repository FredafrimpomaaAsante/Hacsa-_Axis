import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-at-least-thirty-two-chars"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["SEED_ADMIN_EMAIL"] = "admin@hacsa10.example.com"
os.environ["SEED_ADMIN_PASSWORD"] = "Admin123!"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
