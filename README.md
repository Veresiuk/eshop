# E-Shop REST API — Лабораторна робота №8

Асинхронний REST API для вебсервісу управління інтернет-магазином (Варіант №3), розроблений за допомогою **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2** та **HTTPX**.

---

## 📌 Основні можливості

- **Архітектурний підхід:** Розподіл на шари API (FastAPI) $\rightarrow$ Service Layer $\rightarrow$ Repository Layer $\rightarrow$ Database (SQLite/SQLAlchemy).
- **Сутності системи:** Товари (`products`) та категорії (`categories`).
- **Повна підтримка CRUD:** Реалізація методів `GET`, `POST`, `PATCH`, `DELETE` з коректними статус-кодами (`200`, `201`, `204`, `400`, `404`, `409`, `422`).
- **Транзакційна логіка:** Атомарне списання кількості товару зі складу при покупці (`POST /products/{id}/purchase`) з перевіркою залишку.
- **Асинхронність та конкурентність:** Модуль `external_api.py` для паралельного опитування декількох ресурсів з використанням `asyncio.Task`, `asyncio.gather()`, обмеженням паралелізму через `asyncio.Semaphore`, таймаутами (`timeout`) та механізмом повторних спроб (`retry`) з експоненційним backoff.
- **Автоматична документація:** Інтерактивний Swagger UI (`/docs`) та ReDoc (`/redoc`).

---

## 📂 Структура проєкту

```text
eshop/
├── pyproject.toml                     # Конфігурація проєкту та залежностей
├── README.md                          # Документація проєкту
├── report/
│   └── Вересюк_Ірина_Лаб08_V3.pdf     # Звіт з лабораторної роботи
├── src/
│   └── eshop/
│       ├── __init__.py                # Ініціалізація пакета
│       ├── database.py                # Підключення до БД (SQLAlchemy Engine, SessionLocal)
│       ├── models.py                  # Декларативні ORM-моделі (Category, Product)
│       ├── schemas.py                 # Pydantic v2 схеми валідації та серіалізації
│       ├── repositories.py            # Рівень доступу до даних (Repository Layer)
│       ├── services.py                # Бізнес-логіка (покупка, підрахунок залишків)
│       ├── external_api.py            # Асинхронний HTTP-клієнт (Task, gather, Semaphore, retry)
│       └── api.py                     # FastAPI додаток та маршрути (Endpoints)
└── tests/
    ├── conftest.py                    # Налаштування тестового середовища (StaticPool in-memory SQLite)
    └── test_api.py                    # Інтеграційні тести API