from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(50), unique=True, index=True, nullable=False
    )  # Ограничили длину
    password = Column(String(255), nullable=False)

    habits = relationship("Habit", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    periodicity = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="habits")
    checkins = relationship(
        "Checkin", back_populates="habit", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Habit(id={self.id}, name='{self.name}', periodicity={self.periodicity})>"
        )


class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    checkin_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)

    habit = relationship("Habit", back_populates="checkins")


def __repr__(self):
    return (
        f"<Checkin(id={self.id}, habit_id={self.habit_id}, "
        f"date={self.checkin_date}, completed={self.completed})>"
    )
