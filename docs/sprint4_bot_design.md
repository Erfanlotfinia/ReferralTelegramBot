# Sprint 4 — Telegram Bot Design & Implementation Notes

## E) Telegram Bot Design Choices

### Library Choice
**aiogram (async)** is used for the Telegram bot layer.

**Justification**
- Fully async and well-aligned with the async SQLAlchemy backend.
- Clean router/handler separation and concise command filters.
- Minimal boilerplate for polling-based bots while remaining production-ready.

### Command-to-Handler Mapping
- `/start` → `start_handler`
- `/my_status` → `my_status_handler`
- `/ref_summary` → `ref_summary_handler`

### `/start` Payload Parsing Spec
Expected payload format: `ref_<telegram_id>`
- Example: `/start ref_12345`
- Only digits are accepted after `ref_`.
- Case-insensitive prefix (e.g., `REF_12345` accepted).
- Any other payload is treated as invalid and does **not** create a referral.
- The referred user is still upserted even if the payload is invalid.

## G) Minimal Bot Code

### Integration Strategy
**Option A: direct usecase invocation** (shared codebase).

**Why**
- Avoids extra HTTP hop and keeps logic centralized in usecases.
- Ensures a single source of truth for referral idempotency and validation.
- Keeps bot handlers as thin adapters with no DB logic embedded.

### Files
- `bot/main.py`: bot entrypoint, dispatcher setup, polling start.
- `bot/handlers/commands.py`: `/start`, `/my_status`, `/ref_summary` handlers.
- `bot/services.py`: adapter layer calling backend usecases with UnitOfWork.

### Error Handling & Logging
- All handlers catch domain errors (`ValidationError`, `ConflictError`, `NotFoundError`).
- Unexpected errors are logged and return a safe user-facing message.
- Request IDs are set per message to correlate logs.
