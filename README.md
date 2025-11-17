# Habit Tracker API

![CI](https://github.com/GlebEdu/Secure-Development-Course/actions/workflows/ci.yml/badge.svg)

API для отслеживания привычек с аутентификацией, управлением привычками и отметками о выполнении.

## Быстрый старт

```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Установка зависимостей
pip install -r requirements.txt -r requirements-dev.txt

# Установка pre-commit хуков
pre-commit install

# Запуск приложения
uvicorn app.main:app --reload
```

## Тестирование

```bash
# Запуск тестов
pytest -q

```

## Ритуал перед PR

```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## CI/CD

В репозитории настроен workflow **CI** (GitHub Actions) — обязательная проверка для ветки `main`.
Бейдж добавится автоматически после загрузки в GitHub.

## Контейнеризация

```bash
# Сборка образа
docker build -t habit-tracker .

# Запуск контейнера
docker run --rm -p 8000:8000 habit-tracker

# Или через docker-compose
docker-compose up --build
```

## Аутентификация

Перед использованием API необходимо получить токен доступа:

```bash
curl -X POST "http://localhost:8000/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "test_user", "password": "test_password"}'
```

Ответ:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

Используйте токен в заголовках запросов:
```
Authorization: Bearer <your_token>
```

## Эндпоинты API

### Проверка здоровья
- `GET /health` - Проверка статуса приложения и базы данных

### Аутентификация
- `POST /login` - Получение токена доступа
- `GET /users/me` - Информация о текущем пользователе

### Управление привычками
- `POST /habits` - Создать новую привычку
- `GET /habits` - Получить все привычки пользователя
- `GET /habits/{id}` - Получить привычку по ID
- `GET /habits/{id}/detailed` - Получить привычку с отметками о выполнении
- `PUT /habits/{id}` - Обновить привычку
- `DELETE /habits/{id}` - Удалить привычку

### Управление отметками
- `POST /checkins` - Создать отметку о выполнении
- `GET /checkins` - Получить все отметки пользователя
- `GET /checkins/{id}` - Получить отметку по ID
- `PUT /checkins/{id}` - Обновить отметку
- `DELETE /checkins/{id}` - Удалить отметку

### Статистика
- `GET /stats` - Общая статистика по всем привычкам
- `GET /habits/{id}/stats` - Статистика по конкретной привычке


## Формат ошибок

Ошибки возвращаются в формате RFC 7807 с дополнительными полями для трассировки:


```json
{
  "type": "https://habittracker.com/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Habit not found",
  "instance": "/habits/999",
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2024-01-15T10:30:00Z",
  "code": "NOT_FOUND"
}
```

## Безопасность

- Аутентификация через JWT токены
- Защита от XSS через экранирование вывода
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Rate limiting (50 запросов в минуту)
- Валидация входных данных
- Хеширование паролей

## Тестовый пользователь

При запуске приложения автоматически создается тестовый пользователь:
- Логин: `test_user`
- Пароль: `test_password`

## Документация API

После запуска приложения доступна автоматическая документация:
- Swagger UI: http://localhost:8000/docs

---

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`
