# Referral Telegram Bot (Sprint 6)

## Run the API
```bash
docker compose up -d postgres
alembic -c database/alembic.ini upgrade head
cd backend
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Run the Telegram bot
```bash
cd /path/to/ReferralTelegramBot
export BOT_DRY_RUN=1
PYTHONPATH=backend:. python -m bot.main
```
Set `BOT_DRY_RUN=0` and provide `TELEGRAM_BOT_TOKEN` for real polling.

## Sample env file
Copy `.env.example` to `.env` and fill in required values.

## Evaluation criteria
- Correct referral behavior + preventing duplicates (DB unique constraint + conflict handling).
- A clean project structure (even if small).
- Error handling (API / Telegram / DB).
- Executable README (commands that actually work).
