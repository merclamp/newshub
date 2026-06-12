# NewsHub

Агрегатор новостей независимых СМИ: статьи с сайтов в одной ленте, плюс Telegram-бот с периодическими дайджестами.

## Стек

- **Backend**: Python 3.12+, [uv](https://docs.astral.sh/uv/), FastAPI, Redis (единственное хранилище)
- **Бот**: aiogram 3 (дайджесты по подписке)
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

Список источников: `backend/app/sources.py`.

## Быстрый старт (Docker)

```bash
cp .env.example .env        # при необходимости отредактируйте
docker compose up -d --build
```

- Веб-интерфейс: http://localhost:8080
- API (Swagger): http://localhost:8000/docs

### Telegram-бот (опционально)

1. Получите токен у [@BotFather](https://t.me/BotFather) и пропишите его в `.env` (`BOT_TOKEN=...`).
2. Запустите с профилем `bot`:

```bash
docker compose --profile bot up -d
```

Команды бота: `/subscribe`, `/unsubscribe`, `/digest` (сводка прямо сейчас), `/sources`.

## Архитектура

```
┌──────────┐   опрос RSS    ┌─────────┐
│  worker  ├───────────────►│  Redis  │
└──────────┘  каждые 5 мин  └────┬────┘
                                 │
        ┌────────────────┬───────┤
        ▼                ▼       ▼
   ┌─────────┐      ┌─────────┐ ┌──────────┐
   │   api   │      │   bot   │ │ frontend │
   │ FastAPI │      │ aiogram │ │ nginx +  │
   └─────────┘      └─────────┘ │  Svelte  │
        ▲                       └────┬─────┘
        └──────── proxy /api ────────┘
```

- **worker** — опрашивает все фиды конкурентно, дедуплицирует (SET NX), складывает в Redis (hash на статью + sorted set'ы лент, TTL 7 дней). Если фид отдаёт полный текст (`content:encoded`), он сохраняется сразу (с санитизацией HTML через nh3).
- **api** — отдаёт ленту с фильтром по источнику. `GET /api/news/{id}` возвращает полный текст статьи: если его не было в RSS, текст извлекается из оригинальной страницы (trafilatura) при первом запросе и кэшируется в Redis.
- **bot** — шлёт подписчикам дайджест каждые N часов (только новое с прошлого дайджеста).
- **frontend** — SPA на Svelte, nginx проксирует `/api` на backend. Статьи читаются прямо на сайте (модальное окно с полным текстом и ссылкой на оригинал).

## Локальная разработка (без Docker)

Нужен запущенный Redis (`docker run -p 6379:6379 redis:7-alpine`).

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload          # API → :8000
uv run python -m app.worker                   # сборщик
BOT_TOKEN=... uv run python -m app.bot.main   # бот (опционально)

# Frontend (проксирует /api на :8000)
cd frontend
npm install
npm run dev                                   # → :5173
```

## Конфигурация (переменные окружения)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | адрес Redis |
| `FETCH_INTERVAL_SECONDS` | `300` | период опроса источников |
| `ARTICLE_TTL_DAYS` | `7` | сколько хранить материалы |
| `BOT_TOKEN` | — | токен Telegram-бота |
| `DIGEST_INTERVAL_HOURS` | `6` | период рассылки дайджеста |
| `DIGEST_MAX_PER_SOURCE` | `5` | материалов от источника в дайджесте |
| `CORS_ORIGINS` | `*` | разрешённые CORS-источники |

## Как добавить источник

Добавьте запись в `backend/app/sources.py`:

```python
Source(id="my-source", name="Моё СМИ", kind="article",
       url="https://example.org/feed/", homepage="https://example.org"),
```
