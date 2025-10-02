from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .schemas import (
    CheckinCreate,
    CheckinResponse,
    HabitCreate,
    HabitResponse,
    StatsResponse,
)

app = FastAPI(title="Habit Tracker App", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


_DB = {"users": [{"id": 1, "username": "test_user"}], "habits": [], "checkins": []}


@app.post("/habits", response_model=HabitResponse)
def create_habit(habit: HabitCreate):
    """Создать новую привычку"""
    new_habit = {
        "id": len(_DB["habits"]) + 1,
        "name": habit.name,
        "periodicity": habit.periodicity,
        "user_id": 1,  # Использование тестового пользователя
    }
    _DB["habits"].append(new_habit)
    return new_habit


@app.get("/habits", response_model=List[HabitResponse])
def get_habits():
    """Получить все привычки"""
    return _DB["habits"]


@app.get("/habits/{habit_id}", response_model=HabitResponse)
def get_habit(habit_id: int):
    """Получить привычку по ID"""
    for habit in _DB["habits"]:
        if habit["id"] == habit_id:
            return habit
    raise ApiError(code="not_found", message="Habit not found", status=404)


@app.put("/habits/{habit_id}", response_model=HabitResponse)
def update_habit(habit_id: int, habit: HabitCreate):
    """Обновить привычку"""
    for h in _DB["habits"]:
        if h["id"] == habit_id:
            h["name"] = habit.name
            h["periodicity"] = habit.periodicity
            return h
    raise ApiError(code="not_found", message="Habit not found", status=404)


@app.delete("/habits/{habit_id}")
def delete_habit(habit_id: int):
    """Удалить привычку"""
    for i, habit in enumerate(_DB["habits"]):
        if habit["id"] == habit_id:
            # Удаляем связанные отметки
            _DB["checkins"] = [c for c in _DB["checkins"] if c["habit_id"] != habit_id]
            del _DB["habits"][i]
            return {"message": "Habit deleted"}
    raise ApiError(code="not_found", message="Habit not found", status=404)


@app.post("/checkins", response_model=CheckinResponse)
def create_checkin(checkin: CheckinCreate):
    """Создать отметку о выполнении привычки"""
    # Проверяем существование привычки
    habit_exists = any(habit["id"] == checkin.habit_id for habit in _DB["habits"])
    if not habit_exists:
        raise ApiError(code="not_found", message="Habit not found", status=404)

    new_checkin = {
        "id": len(_DB["checkins"]) + 1,
        "habit_id": checkin.habit_id,
        "checkin_date": checkin.checkin_date,
        "completed": checkin.completed,
    }
    _DB["checkins"].append(new_checkin)
    return new_checkin


@app.get("/checkins", response_model=List[CheckinResponse])
def get_checkins():
    """Получить все отметки"""
    return _DB["checkins"]


@app.get("/checkins/{checkin_id}", response_model=CheckinResponse)
def get_checkin(checkin_id: int):
    """Получить отметку по ID"""
    for checkin in _DB["checkins"]:
        if checkin["id"] == checkin_id:
            return checkin
    raise ApiError(code="not_found", message="Checkin not found", status=404)


@app.put("/checkins/{checkin_id}", response_model=CheckinResponse)
def update_checkin(checkin_id: int, checkin: CheckinCreate):
    """Обновить отметку"""
    for c in _DB["checkins"]:
        if c["id"] == checkin_id:
            c["habit_id"] = checkin.habit_id
            c["checkin_date"] = checkin.checkin_date
            c["completed"] = checkin.completed
            return c
    raise ApiError(code="not_found", message="Checkin not found", status=404)


@app.delete("/checkins/{checkin_id}")
def delete_checkin(checkin_id: int):
    """Удалить отметку"""
    for i, checkin in enumerate(_DB["checkins"]):
        if checkin["id"] == checkin_id:
            del _DB["checkins"][i]
            return {"message": "Checkin deleted"}
    raise ApiError(code="not_found", message="Checkin not found", status=404)


@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """Получить общую статистику по привычкам"""
    total_habits = len(_DB["habits"])
    total_checkins = len(_DB["checkins"])
    completed_checkins = len([c for c in _DB["checkins"] if c["completed"]])

    completion_rate = 0.0
    if total_checkins > 0:
        completion_rate = round((completed_checkins / total_checkins) * 100, 2)

    return StatsResponse(
        total_habits=total_habits,
        total_checkins=total_checkins,
        completed_checkins=completed_checkins,
        completion_rate=completion_rate,
    )
