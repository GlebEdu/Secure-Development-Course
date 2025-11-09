import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет совпадение пароля с хешем
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Создает безопасный хеш пароля
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен с указанными данными
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Аутентифицирует пользователя с помощью безопасного запроса к БД
    """
    # используется ORM - защита от SQL injection
    user = db.query(User).filter(User.username == username).first()

    if not user:
        # Логируем попытку входа несуществующего пользователя
        print(f"Failed login attempt for non-existent user: {username}")
        return None

    if not verify_password(password, user.password):
        # Логируем неверный пароль
        masked_username = f"{username[:3]}***" if len(username) > 3 else "***"
        print(f"Failed login for user: {masked_username}")
        return None

    # Успешная аутентификация
    print(f"Successful login for user: {username}")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Извлекает и проверяет текущего пользователя из JWT токена
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем JWT токен
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError as e:
        print(f"JWT decoding error: {e}")
        raise credentials_exception

    # безопасно ищем пользователя в БД
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        print(f"User not found for token: {username}")
        raise credentials_exception

    return user
