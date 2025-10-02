# tests/conftest.py
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import _DB, app  # noqa: E402


@pytest.fixture(autouse=True)
def cleanup_database():
    """Очистка базы данных перед каждым тестом"""
    _DB["habits"].clear()
    _DB["checkins"].clear()
    yield


@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    return TestClient(app)


@pytest.fixture
def sample_habit(client):
    """Фикстура для создания тестовой привычки"""
    habit_data = {"name": "Тестовая привычка", "periodicity": 1}
    response = client.post("/habits", json=habit_data)
    return response.json()


@pytest.fixture
def sample_checkin(client, sample_habit):
    """Фикстура для создания тестовой отметки"""
    checkin_data = {
        "habit_id": sample_habit["id"],
        "checkin_date": "2025-09-01",
        "completed": True,
    }
    response = client.post("/checkins", json=checkin_data)
    return response.json()
