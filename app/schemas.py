from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class HabitCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Название привычки"
    )
    periodicity: int = Field(..., gt=0, description="Периодичность (в днях)")


class HabitResponse(BaseModel):
    id: int
    name: str
    periodicity: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class CheckinCreate(BaseModel):
    habit_id: int = Field(..., gt=0, description="ID привычки")
    checkin_date: date = Field(..., description="Дата отметки")
    completed: bool = Field(..., description="Выполнено (да/нет)")


class CheckinResponse(BaseModel):
    id: int
    habit_id: int
    checkin_date: date
    completed: bool

    model_config = ConfigDict(from_attributes=True)


class StatsResponse(BaseModel):
    total_habits: int
    total_checkins: int
    completed_checkins: int
    completion_rate: float


class HabitWithCheckins(HabitResponse):
    """Схема привычки с списком отметок"""

    checkins: List[CheckinResponse] = []


class UserCreate(BaseModel):
    username: str = Field(
        ..., min_length=1, max_length=50, description="Имя пользователя"
    )


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
