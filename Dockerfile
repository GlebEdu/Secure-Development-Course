# Multi-stage build
FROM python:3.11-slim AS builder

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Тестовая стадия
FROM python:3.11-slim AS tester

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app app

# Копирование виртуального окружения из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создание директорий для данных
RUN mkdir -p /app/data && chown -R app:app /app

# Установка тестовых зависимостей
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

WORKDIR /app
COPY --chown=app:app . .

USER app

# Финальный образ (без изменений)
FROM python:3.11-slim

# Метаданные
LABEL description="Habit Tracker API"
LABEL version="1.0.0"

# Установка только runtime зависимостей + curl для healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app app

# Копирование виртуального окружения из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создание рабочих директорий
RUN mkdir -p /app/data && chown -R app:app /app

WORKDIR /app

# Копирование приложения с правильными правами
COPY --chown=app:app ./app ./app
COPY --chown=app:app requirements.txt .

# Переключаемся на не-root пользователя
USER app

# Явное объявление точки входа
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Healthcheck с curl (проверяет эндпоинт /health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
