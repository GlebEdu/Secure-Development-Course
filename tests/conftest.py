# tests/conftest.py
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Checkin, Habit, User  # noqa: E402

# Тестовая база данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Переопределение зависимости базы данных для тестов"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Создание и очистка тестовой базы данных для каждого теста"""
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Создаем тестового пользователя
    test_user = User(username="test_user")
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    yield db

    # Очищаем базу после теста
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Фикстура для тестового клиента"""
    return TestClient(app)


@pytest.fixture
def sample_habit(client, test_db):
    """Фикстура для создания тестовой привычки"""
    habit_data = {"name": "Тестовая привычка", "periodicity": 1}
    response = client.post("/habits", json=habit_data)
    return response.json()


@pytest.fixture
def sample_checkin(client, sample_habit, test_db):
    """Фикстура для создания тестовой отметки"""
    checkin_data = {
        "habit_id": sample_habit["id"],
        "checkin_date": "2025-09-01",
        "completed": True,
    }
    response = client.post("/checkins", json=checkin_data)
    return response.json()


@pytest.fixture
def test_user(test_db):
    """Фикстура для тестового пользователя"""
    user = test_db.query(User).filter(User.username == "test_user").first()
    return user


@pytest.fixture(autouse=True)
def cleanup_database(test_db):
    """Очистка базы данных перед каждым тестом"""
    # Удаляем все данные кроме тестового пользователя
    test_db.query(Checkin).delete()
    test_db.query(Habit).delete()
    test_db.commit()
    yield
