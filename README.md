# Referral Telegram Bot
Simple FastAPI + Telegram bot for tracking referrals.

## Requirements
- Python 3.14
- Postgres

## Run the API
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

docker compose up -d postgres
alembic -c database/alembic.ini upgrade head
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Run the Telegram bot
```bash
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

export BOT_DRY_RUN=1
PYTHONPATH=backend:. python -m bot.main
```

## Env sample
Copy `.env.example` to `.env` and fill in values.

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
