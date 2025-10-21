from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import Integer, func, text
from sqlalchemy.orm import Session

from .database import engine, get_db
from .errorsRFC7807 import (
    ApiError,
    api_error_handler,
    general_exception_handler,
    http_exception_handler,
)
from .models import Base, Checkin, Habit, User
from .rate_limit import init_rate_limiting, limiter
from .schemas import (
    CheckinCreate,
    CheckinResponse,
    HabitCreate,
    HabitResponse,
    HabitWithCheckins,
    StatsResponse,
)


def init_test_user(db: Session):
    """Инициализация тестового пользователя"""
    try:
        test_user = db.query(User).filter(User.username == "test_user").first()
        if not test_user:
            test_user = User(username="test_user")
            db.add(test_user)
            db.commit()
            print("Test user created")
        else:
            print("Test user already exists")
    except Exception as e:
        print(f"Error during startup: {e}")
        db.rollback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager для инициализации при запуске и очистки при завершении"""
    print("Starting up...")

    Base.metadata.create_all(bind=engine)
    print("Database tables created")

    db = next(get_db())
    init_test_user(db)
    yield

    print("Shutting down...")


app = FastAPI(title="Habit Tracker App", version="0.1.0", lifespan=lifespan)
app = init_rate_limiting(app)

# Регистрируем обработчики ошибок
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/health")
@limiter.limit("50/minute")
def health(request: Request, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        print(f"DB test result: {result}")

        tables = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
        print(f"Available tables: {[t[0] for t in tables]}")

        db.commit()
        db_status = "connected"
    except Exception as e:
        print(f"DB health check error: {e}")
        db.rollback()
        db_status = f"disconnected: {str(e)}"

    return {"status": "ok", "database": db_status}


# Habit Endpoints
@app.post("/habits", response_model=HabitResponse)
def create_habit(habit: HabitCreate, db: Session = Depends(get_db)):
    """Создать новую привычку"""
    # Используем тестового пользователя (id=1)
    db_habit = Habit(name=habit.name, periodicity=habit.periodicity, user_id=1)

    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)

    return db_habit


@app.get("/habits", response_model=List[HabitResponse])
def get_habits(db: Session = Depends(get_db)):
    """Получить все привычки"""
    habits = db.query(Habit).filter(Habit.user_id == 1).all()
    return habits


@app.get("/habits/{habit_id}", response_model=HabitResponse)
def get_habit(habit_id: int, db: Session = Depends(get_db)):
    """Получить привычку по ID"""
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == 1).first()

    if not habit:
        raise ApiError(code="NOT_FOUND", message="Habit not found", status=404)

    return habit


@app.get("/habits/{habit_id}/detailed", response_model=HabitWithCheckins)
def get_habit_detailed(habit_id: int, db: Session = Depends(get_db)):
    """Получить привычку по ID с всеми отметками"""
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == 1).first()

    if not habit:
        raise ApiError(code="NOT_FOUND", message="Habit not found", status=404)

    return habit


@app.put("/habits/{habit_id}", response_model=HabitResponse)
def update_habit(habit_id: int, habit: HabitCreate, db: Session = Depends(get_db)):
    """Обновить привычку"""
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == 1).first()

    if not db_habit:
        raise ApiError(code="NOT_FOUND", message="Habit not found", status=404)

    db_habit.name = habit.name
    db_habit.periodicity = habit.periodicity

    db.commit()
    db.refresh(db_habit)

    return db_habit


@app.delete("/habits/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    """Удалить привычку"""
    db_habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == 1).first()

    if not db_habit:
        raise ApiError(code="NOT_FOUND", message="Habit not found", status=404)

    db.delete(db_habit)
    db.commit()

    return {"message": "Habit deleted"}


# Checkin Endpoints
@app.post("/checkins", response_model=CheckinResponse)
def create_checkin(checkin: CheckinCreate, db: Session = Depends(get_db)):
    """Создать отметку о выполнении привычки"""
    habit = (
        db.query(Habit).filter(Habit.id == checkin.habit_id, Habit.user_id == 1).first()
    )

    if not habit:
        raise ApiError(code="NOT_FOUND", message="Habit not found", status=404)

    existing_checkin = (
        db.query(Checkin)
        .filter(
            Checkin.habit_id == checkin.habit_id,
            Checkin.checkin_date == checkin.checkin_date,
        )
        .first()
    )

    if existing_checkin:
        raise ApiError(
            code="DUPLICATE_CHECKIN",
            message="Checkin already exists for this date",
            status=400,
        )

    db_checkin = Checkin(
        habit_id=checkin.habit_id,
        checkin_date=checkin.checkin_date,
        completed=checkin.completed,
    )

    db.add(db_checkin)
    db.commit()
    db.refresh(db_checkin)

    return db_checkin


@app.get("/checkins", response_model=List[CheckinResponse])
def get_checkins(db: Session = Depends(get_db)):
    """Получить все отметки"""
    # Получаем только отметки для привычек текущего пользователя
    checkins = db.query(Checkin).join(Habit).filter(Habit.user_id == 1).all()
    return checkins


@app.get("/checkins/{checkin_id}", response_model=CheckinResponse)
def get_checkin(checkin_id: int, db: Session = Depends(get_db)):
    """Получить отметку по ID"""
    checkin = (
        db.query(Checkin)
        .join(Habit)
        .filter(Checkin.id == checkin_id, Habit.user_id == 1)
        .first()
    )

    if not checkin:
        raise ApiError(code="NOT_FOUND", message="Checkin not found", status=404)

    return checkin


@app.put("/checkins/{checkin_id}", response_model=CheckinResponse)
def update_checkin(
    checkin_id: int, checkin: CheckinCreate, db: Session = Depends(get_db)
):
    """Обновить отметку"""
    db_checkin = (
        db.query(Checkin)
        .join(Habit)
        .filter(Checkin.id == checkin_id, Habit.user_id == 1)
        .first()
    )

    if not db_checkin:
        raise ApiError(code="NOT_FOUND", message="Checkin not found", status=404)

    if db_checkin.habit_id != checkin.habit_id:
        new_habit = (
            db.query(Habit)
            .filter(Habit.id == checkin.habit_id, Habit.user_id == 1)
            .first()
        )

        if not new_habit:
            raise ApiError(code="NOT_FOUND", message="Habit not found", status=404)

    if (
        db_checkin.habit_id != checkin.habit_id
        or db_checkin.checkin_date != checkin.checkin_date
    ):
        existing_checkin = (
            db.query(Checkin)
            .filter(
                Checkin.habit_id == checkin.habit_id,
                Checkin.checkin_date == checkin.checkin_date,
                Checkin.id != checkin_id,
            )
            .first()
        )

        if existing_checkin:
            raise ApiError(
                code="DUPLICATE_CHECKIN",
                message="Checkin already exists for this date",
                status=400,
            )

    db_checkin.habit_id = checkin.habit_id
    db_checkin.checkin_date = checkin.checkin_date
    db_checkin.completed = checkin.completed

    db.commit()
    db.refresh(db_checkin)

    return db_checkin


@app.delete("/checkins/{checkin_id}")
def delete_checkin(checkin_id: int, db: Session = Depends(get_db)):
    """Удалить отметку"""
    checkin = (
        db.query(Checkin)
        .join(Habit)
        .filter(Checkin.id == checkin_id, Habit.user_id == 1)
        .first()
    )

    if not checkin:
        raise ApiError(code="NOT_FOUND", message="Checkin not found", status=404)

    db.delete(checkin)
    db.commit()

    return {"message": "Checkin deleted"}


# Stats Endpoints
@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Получить общую статистику по привычкам"""
    # Статистика привычек
    total_habits = db.query(Habit).filter(Habit.user_id == 1).count()

    # Статистика отметок
    checkin_stats = (
        db.query(
            func.count(Checkin.id).label("total"),
            func.sum(func.cast(Checkin.completed, Integer)).label("completed"),
        )
        .join(Habit)
        .filter(Habit.user_id == 1)
        .first()
    )

    total_checkins = checkin_stats.total or 0
    completed_checkins = checkin_stats.completed or 0

    completion_rate = 0.0
    if total_checkins > 0:
        completion_rate = round((completed_checkins / total_checkins) * 100, 2)

    return StatsResponse(
        total_habits=total_habits,
        total_checkins=total_checkins,
        completed_checkins=completed_checkins,
        completion_rate=completion_rate,
    )


@app.get("/habits/{habit_id}/stats")
def get_habit_stats(habit_id: int, db: Session = Depends(get_db)):
    """Получить статистику по конкретной привычке"""
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == 1).first()

    if not habit:
        raise ApiError(code="NOT_FOUND", message="Habit not found", status=404)

    checkin_stats = (
        db.query(
            func.count(Checkin.id).label("total"),
            func.sum(func.cast(Checkin.completed, Integer)).label("completed"),
        )
        .join(Habit)
        .filter(Habit.user_id == 1)
        .first()
    )

    total_checkins = checkin_stats.total or 0
    completed_checkins = checkin_stats.completed or 0

    completion_rate = 0.0
    if total_checkins > 0:
        completion_rate = round((completed_checkins / total_checkins) * 100, 2)

    return {
        "habit_id": habit_id,
        "habit_name": habit.name,
        "total_checkins": total_checkins,
        "completed_checkins": completed_checkins,
        "completion_rate": completion_rate,
        "periodicity": habit.periodicity,
    }
