# DFD — Data Flow Diagram (шаблон)

## Диаграмма (Mermaid)
```mermaid
%% DFD — Habit Tracker App
flowchart TD

%% ==== Trust Boundaries ====
subgraph Client[Клиент Браузер Мобильное приложение Trust Boundary: Client]
    A1[UI / Frontend React, Mobile App]
end

subgraph Edge["Edge Layer / API Gateway\n[Trust Boundary: Edge]"]
    B1["FastAPI App\n(main.py)\n(REST API over HTTPS)"]
end

subgraph Core["Core Logic Layer\n[Trust Boundary: Core]"]
    C1["Habits Service\n(CRUD + Validation)"]
    C2["Checkins Service\n(CRUD + Validation)"]
    C3["Stats Service\n(Аналитика / Aggregation)"]
    C4["Error Handler & Logger\n(ApiError / Exception)"]
end

subgraph Data["Data Layer\n[Trust Boundary: Data]"]
    D1["In-Memory DB (dict _DB)\n→ позже SQLite/PostgreSQL"]
end

%% ==== External Systems ====
E1["Monitoring / Grafana\n(NFR-02, NFR-07)"]
E2["Log Collector / ELK Stack"]

%% ==== Flows ====
A1 -- "F1: HTTP(S) Request (JSON)\nGET /health, /habits, /checkins, /stats" --> B1
B1 -- "F2: Internal Call\n(Validate → Route → Call Core)" --> C1
B1 -- "F3: Internal Call\n(Create/Update/Delete Checkin)" --> C2
B1 -- "F4: Internal Call\n(Get Stats)" --> C3
B1 -- "F5: Error/Exception → Handler" --> C4

C1 -- "F6: CRUD операции с привычками" --> D1
C2 -- "F7: CRUD операции с отметками" --> D1
C3 -- "F8: Агрегация данных (Stats)\n(SELECT habits + checkins)" --> D1

C4 -- "F9: Логирование ошибок\n(JSON w/ timestamp, request_id)" --> E2
B1 -- "F10: Метрики состояния\n(health, uptime, latency)" --> E1

B1 -- "F11: HTTP(S) Response (JSON)\n(status/data/error envelope)" --> A1

```

## Список потоков

| ID | Откуда → Куда | Канал/Протокол | Данные/PII | Комментарий |
|----|---------------|-----------------|------------|-------------|
| F1  | Клиент → FastAPI App             | HTTPS                  | habit data, creds                 | Вызов REST API: /health, /habits, /checkins, /stats |
| F2  | FastAPI App → Habits Service     | Internal (Python call)  | habit payload                    | Создание, чтение, обновление привычек |
| F3  | FastAPI App → Checkins Service   | Internal (Python call)  | checkin payload                   | CRUD операций с отметками выполнения |
| F4  | FastAPI App → Stats Service      | Internal (Python call)  | aggregated habit/checkin data     | Расчёт агрегированной статистики |
| F5  | FastAPI App → Error Handler      | Internal (Exception)    | error info                        | Обработка и нормализация ошибок |
| F6  | Habits Service → In-Memory DB    | In-memory (direct)      | habit records                     | CRUD операции с привычками |
| F7  | Checkins Service → In-Memory DB  | In-memory (direct)      | checkin records                   | CRUD операции с отметками |
| F8  | Stats Service → In-Memory DB     | In-memory (direct)      | habit + checkin data              | Вычисление completion_rate |
| F9  | Error Handler → Log Collector    | HTTP / JSON logs        | error metadata (timestamp, id)    | Логирование ошибок в ELK Stack |
| F10 | FastAPI App → Monitoring System  | HTTP / Prometheus Export| metrics only (no PII)             | Отправка метрик в Grafana/Prometheus |
| F11 | FastAPI App → Клиент             | HTTPS (REST JSON)       | response data (no PII)            | Ответ пользователю в формате {"error": {...}} или data |
