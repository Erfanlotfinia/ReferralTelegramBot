# Sprint 5: Run/Deploy Guide (API, Bot, Worker)

## Design choices (minimal + robust)
- **Worker scheduling**: asyncio loop with `sleep(300)` for simplicity and fewer dependencies; APScheduler would be heavier than needed for a single 5‑minute cadence.
- **Price state persistence**: stored in the DB (price_samples) so last price survives restarts and prevents duplicate alerts after restarts.

## Environment variables

**Core**
- `DATABASE_URL` (e.g. `postgresql+asyncpg://postgres:postgres@postgres:5432/referrals`)

**Bot**
- `TELEGRAM_BOT_TOKEN` (required for the bot and worker notifications)

**Worker**
- `TELEGRAM_ALERT_CHAT_ID` (Telegram channel or chat ID for alerts)
- `PRICE_ALERT_SYMBOL` (default: `BTC-USD`)
- `PRICE_ALERT_THRESHOLD` (default: `0.01` = 1%)
- `PRICE_ALERT_INTERVAL_SECONDS` (default: `300`)
- `PRICE_ALERT_API_URL` (default: `https://api.coinbase.com/v2/prices/{symbol}/spot`)

If `TELEGRAM_BOT_TOKEN` or `TELEGRAM_ALERT_CHAT_ID` is missing, the worker will log alerts instead of sending them.

## Local run (Docker Compose)

```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_ALERT_CHAT_ID="@your_channel_or_chat_id"
docker compose up --build
```

Services:
- **api**: FastAPI on `http://localhost:8000`
- **bot**: Telegram polling bot
- **worker**: Price alert worker (5‑minute cycle)
- **postgres**: database

## Local run (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/referrals"
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_ALERT_CHAT_ID="@your_channel_or_chat_id"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
python -m bot.main
python -m app.worker.main
```

## Applying DB migrations

If you use Alembic, apply migrations from `database/alembic/versions` (create an `alembic.ini`
in your environment as needed). The latest migration adds `price_samples` and the self‑referral
check constraint.
