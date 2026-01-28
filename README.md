# Referral Telegram Bot
Simple FastAPI + Telegram bot for tracking referrals.

## Requirements
- Python 3.14
- Postgres

## Environment
Copy `.env.example` to `.env` and update the values (especially `DATABASE_URL` and
`TELEGRAM_BOT_TOKEN`). You can also export variables directly in your shell.

Key variables:
- `DATABASE_URL` (default local Postgres: `postgresql+asyncpg://postgres:postgres@localhost:5432/referrals`)
- `TELEGRAM_BOT_TOKEN` (required for the Telegram bot)
- `BOT_DRY_RUN=1` to start the bot without polling Telegram (optional for local smoke tests)

## Run with Docker Compose (API + Bot + Worker + Postgres)
```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_ALERT_CHAT_ID="@your_channel_or_chat_id"
docker compose up --build
```

Services:
- **api**: FastAPI on `http://localhost:8000`
- **bot**: Telegram polling bot
- **worker**: price alert worker
- **postgres**: database

## Run locally (without Docker)
### 1) Set up the environment
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### 2) Start Postgres (local or via Docker)
```bash
docker compose up -d postgres
```

### 3) Apply migrations
```bash
alembic -c database/alembic.ini upgrade head
```

### 4) Run the API
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/referrals"
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5) Run the Telegram bot
```bash
export TELEGRAM_BOT_TOKEN="your-token"
export BOT_DRY_RUN=1
PYTHONPATH=backend:. python -m bot.main
```

### Optional: run the worker
```bash
export TELEGRAM_ALERT_CHAT_ID="@your_channel_or_chat_id"
PYTHONPATH=backend python -m app.worker.main
```

## Run tests
```bash
. .venv/bin/activate
pytest -q
```

## Evaluation criteria
- Referral works correctly and prevents duplicates
- Project structure exists (even small)
- Error handling across API / Telegram / DB
- Runnable README
