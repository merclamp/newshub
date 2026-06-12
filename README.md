# NewsHub

Агрегатор новостей независимых СМИ: статьи с сайтов в одной ленте.

## Стек

- **Backend**: Python 3.12+, [uv](https://docs.astral.sh/uv/), FastAPI, Redis (единственное хранилище)
- **Frontend**: Svelte 5, Vite, Bootstrap 5
- **Инфраструктура**: Docker, Docker Compose

## Источники

| Источник | Статьи (RSS) |
|---|---|
| DW Россия | ✓ |
| Meduza | ✓ |
| Дождь | ✓ |
| Ходорковский | ✓ |
| Рабкор | ✓ |
| NewsMaker | ✓ |
| Настоящее Время | ✓ |
| Радио Свобода | ✓ |
| ОВД-Инфо | ✓ |

Список источников: `backend/app/sources.py`.

## Быстрый старт (Docker)

```bash
cp .env.example .env        # при необходимости отредактируйте
docker compose up -d --build
```

- Веб-интерфейс: http://localhost:8080
- API (Swagger): http://localhost:8000/docs

## Архитектура

```
┌──────────┐   опрос RSS    ┌─────────┐
│  worker  ├───────────────►│  Redis  │
└──────────┘   каждый час    └────┬────┘
                                 │
              ┌──────────────────┤
              ▼                  ▼
         ┌─────────┐       ┌──────────┐
         │   api   │       │ frontend │
         │ FastAPI │       │ nginx +  │
         └─────────┘       │  Svelte  │
              ▲            └────┬─────┘
              └── proxy /api ───┘
```

- **worker** — опрашивает все фиды конкурентно, дедуплицирует (SET NX), складывает в Redis (hash на статью + sorted set'ы лент, TTL 7 дней). Если фид отдаёт полный текст (`content:encoded`), он сохраняется сразу (с санитизацией HTML через nh3).
- **api** — отдаёт ленту с фильтром по источнику. `GET /api/news/{id}` возвращает полный текст статьи: если его не было в RSS, текст извлекается из оригинальной страницы (trafilatura) при первом запросе и кэшируется в Redis.
- **frontend** — SPA на Svelte, nginx проксирует `/api` на backend. Статьи читаются прямо на сайте (модальное окно с полным текстом и ссылкой на оригинал).

## Локальная разработка (без Docker)

Нужен запущенный Redis (`docker run -p 6379:6379 redis:7-alpine`).

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload          # API → :8000
uv run python -m app.worker                   # сборщик

# Frontend (проксирует /api на :8000)
cd frontend
npm install
npm run dev                                   # → :5173
```

## Конфигурация (переменные окружения)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | адрес Redis |
| `FETCH_INTERVAL_SECONDS` | `3600` | период опроса источников (сек) |
| `ARTICLE_TTL_DAYS` | `7` | сколько хранить материалы |
| `CORS_ORIGINS` | `*` | разрешённые CORS-источники |

## Как добавить источник

Добавьте запись в `backend/app/sources.py`:

```python
Source(id="my-source", name="Моё СМИ", kind="article",
       url="https://example.org/feed/", homepage="https://example.org"),
```
