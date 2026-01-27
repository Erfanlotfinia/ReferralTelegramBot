# Telegram Referral Bot + FastAPI Backend System Design (Sprint 1)

## Assumptions
- Telegram IDs are integers that fit into 64-bit signed range; store as `BIGINT` for compactness and indexing performance.
- The bot and API are owned by the same team and can share a deployment pipeline.
- Only one referrer per referred user is allowed.
- The referral code format is `ref_<telegram_id>` (numeric ID).
- If the referrer is not in `users` yet, we still allow the referral but will upsert the referrer user on demand (policy described below).

## Architecture Choice
**Monolith (bot + API + DB) with a single FastAPI service**, hosting:
- Telegram bot webhook handler (or long polling runner) for `/start`, `/my_status`, `/ref_summary`.
- REST API for `/users`, `/referrals` endpoints (used by the bot internally and optionally by external clients).
- PostgreSQL database.

**Justification**
- Small scope and tight coupling between bot and API; monolith reduces operational complexity.
- Consistent transactional logic and shared idempotency strategy.
- Faster delivery for Sprint 1 with a clean path to future separation if load grows.

## High-Level Components
1. **FastAPI service**
   - Telegram bot handler (webhook endpoint, e.g., `POST /bot/webhook`).
   - API endpoints (`/users`, `/referrals`).
   - Shared service layer for user/referral logic.
2. **PostgreSQL**
   - `users` table with unique `telegram_id`.
   - `referrals` table with unique `referred_telegram_id`.
3. **Observability**
   - Structured logs with correlation IDs.
   - `/healthz` endpoint.

## Main Flows (Sequence)

### 1) `/start` without ref
1. Telegram sends `/start` to bot webhook.
2. Bot extracts `telegram_id`.
3. Bot calls `POST /users/upsert` with `telegram_id`.
4. API upserts the user in DB (`users` table).
5. Bot replies: welcome + instructions.

### 2) `/start ref_XXXX`
1. Telegram sends `/start ref_12345`.
2. Bot extracts `referrer_telegram_id=12345`, `referred_telegram_id=<current user>`.
3. Bot calls `POST /users/upsert` for the referred user.
4. Bot calls `POST /referrals` with referrer + referred.
5. API validates rules, inserts referral if not present (idempotent).
6. Bot responds: success or already referred.

### 3) `/my_status`
1. Bot calls `GET /users/{telegram_id}/status`.
2. API returns user record + referrer_telegram_id (nullable).
3. Bot formats and sends status.

### 4) `/ref_summary`
1. Bot calls `GET /referrals/{referrer_telegram_id}/summary`.
2. API counts total referrals and returns last 5.
3. Bot shows summary if `count > 0`, otherwise message that user is not a referrer.

### 5) API Calls
- **POST /users/upsert**
  - Inserts user if new; returns existing if already present.
- **POST /referrals**
  - Validates rules and inserts referral if unique and not self-referral.
  - Idempotent: if referral already exists, returns a 200/409 with consistent response.
- **GET /users/{telegram_id}/status**
  - Returns user + referrer (nullable).
- **GET /referrals/{referrer_telegram_id}/summary**
  - Returns count + last 5 referrals sorted by created_at desc.

## Threats, Edge Cases, and Policies

### Race conditions: concurrent `/start`
- Use `INSERT ... ON CONFLICT DO NOTHING` for users.
- Referrals use unique constraint on `referred_telegram_id` to prevent duplicates.
- The API handles insert conflicts and returns idempotent responses.

### Idempotency for referrals
- Policy: `POST /referrals` is idempotent for the same `referred_telegram_id`.
- If a referral already exists:
  - Return `200 OK` with existing referral metadata, or `409 Conflict` if the referrer differs.
- This ensures `/start ref_XXXX` can be retried safely.

### Referrer not in Users
- Policy: allow referral if referrer not present; create user record for referrer via upsert.
- Rationale: referrer may not have started the bot yet but can still receive credit.

### referrer == referred
- Enforced at DB constraint and application validation; API returns `400 Bad Request`.

### Duplicate referral attempts
- DB unique constraint on `referred_telegram_id` prevents multiple referrals.
- API returns idempotent response with existing referral when appropriate.

### Invalid ref code
- If payload is malformed or non-numeric: bot responds with instructions and does not create referral.

## Non-Functional Decisions

### Logging + Correlation ID
- Generate a correlation ID per incoming bot update and propagate to API requests (HTTP header `X-Request-ID`).
- Include correlation ID, telegram_id, and action in logs.

### Error Handling
- API returns JSON with `error_code` + `message`.
- Bot translates errors into friendly user messages.

### Config via Env
- `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `LOG_LEVEL`, `WEBHOOK_SECRET`.

### Migration Strategy
- Use Alembic; migrations live with FastAPI service.
- CI applies migrations on deploy.

### Minimal Observability
- `/healthz` endpoint for readiness/liveness checks.
- Optional basic metrics (request counts/latency).

## API Design

### 1) POST /users/upsert
**Request**
```json
{ "telegram_id": 12345 }
```
**Response**
```json
{ "telegram_id": 12345, "created_at": "2024-01-01T00:00:00Z" }
```

### 2) POST /referrals
**Request**
```json
{ "referrer_telegram_id": 12345, "referred_telegram_id": 99999 }
```
**Response (created)**
```json
{ "referrer_telegram_id": 12345, "referred_telegram_id": 99999, "created_at": "..." }
```
**Response (idempotent existing)**
```json
{ "referrer_telegram_id": 12345, "referred_telegram_id": 99999, "created_at": "...", "status": "already_referred" }
```

### 3) GET /users/{telegram_id}/status
**Response**
```json
{
  "telegram_id": 99999,
  "referrer_telegram_id": 12345,
  "created_at": "..."
}
```

### 4) GET /referrals/{referrer_telegram_id}/summary
**Response**
```json
{
  "count": 10,
  "last_5_referrals": [
    { "telegram_id": 111, "created_at": "..." },
    { "telegram_id": 222, "created_at": "..." }
  ]
}
```

## DB Design (PostgreSQL)

### DDL
```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  telegram_id BIGINT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE referrals (
  id BIGSERIAL PRIMARY KEY,
  referrer_telegram_id BIGINT NOT NULL,
  referred_telegram_id BIGINT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT referrals_referrer_not_referred
    CHECK (referrer_telegram_id <> referred_telegram_id)
);

CREATE INDEX referrals_referrer_created_at_idx
  ON referrals (referrer_telegram_id, created_at DESC);
```

### Foreign Key Strategy
- **Optional FK constraints** (if you want strict referential integrity):
  - `referrals.referrer_telegram_id` → `users.telegram_id`
  - `referrals.referred_telegram_id` → `users.telegram_id`
- If allowing referrals before the referrer starts the bot, either:
  - Upsert referrer on referral creation; or
  - Defer FKs and insert users first.
- In Sprint 1, **recommend upserting both referrer and referred** before insert to keep FKs consistent.

### Key Queries + Indexes

#### User Status
```sql
SELECT u.telegram_id,
       r.referrer_telegram_id,
       u.created_at
FROM users u
LEFT JOIN referrals r
  ON r.referred_telegram_id = u.telegram_id
WHERE u.telegram_id = $1;
```
- Indexes used:
  - `users.telegram_id` unique index.
  - `referrals.referred_telegram_id` unique index.

#### Referral Summary
```sql
SELECT COUNT(*)
FROM referrals
WHERE referrer_telegram_id = $1;

SELECT referred_telegram_id AS telegram_id, created_at
FROM referrals
WHERE referrer_telegram_id = $1
ORDER BY created_at DESC
LIMIT 5;
```
- Index used: `referrals_referrer_created_at_idx`.

## Concurrency + Idempotency (Implementation Notes)
- **User upsert**: `INSERT INTO users (telegram_id) VALUES ($1) ON CONFLICT DO NOTHING`.
- **Referral insert**:
  - Upsert referrer/referred users first.
  - Attempt insert; if unique violation on `referred_telegram_id`:
    - Fetch existing referral and return idempotent response.
  - If `referrer_telegram_id == referred_telegram_id`, reject before DB write.

## Security Notes
- Validate Telegram webhook signature (if using webhook mode).
- Rate-limit bot and API endpoints (IP-based for API, Telegram update-based for bot).
- Secrets stored in environment variables.

## Summary of How Requirements Are Met
- Duplicate referrals prevented by `referrals.referred_telegram_id` unique constraint and idempotent API responses.
- Self-referrals blocked at both app validation and DB check constraint.
- Summary queries optimized with composite index for referrer and created_at ordering.

---

# Sprint 2 Deliverables: Clean Architecture Blueprint + Project Skeleton

## Assumptions (Sprint 2)
- Async Python stack (FastAPI + async DB driver/ORM) will be used for infrastructure.
- Telegram bot handler will call use cases directly (or via an adapter), not via HTTP, to avoid unnecessary network hop.
- Worker is a future component and will be introduced as a separate adapter that also calls use cases.
- Domain entities are pure Python and contain no framework, DB, or Telegram code.

## C) Clean Architecture Design (Explicit and Strict)

### Layer Definitions and Responsibilities
1) **Domain (Entities / Value Objects)**
   - Business rules and invariants.
   - Entities: `User`, `Referral`.
   - Value Objects: `TelegramId` (optional), `ReferralCode` (optional).
   - **No** DB, HTTP, or Telegram dependencies.

2) **Use Cases (Interactors)**
   - Application-specific business rules and orchestration.
   - Implements primary use cases:
     - `UpsertUser`
     - `CreateReferral` (idempotent)
     - `GetUserStatus`
     - `GetReferralSummary`
   - Talks only to interfaces/contracts (repositories, unit of work, clock).
   - Returns DTOs or response models suitable for presenters.

3) **Interface Adapters (Controllers / Presenters / Bot Handlers)**
   - Translate inputs (HTTP requests, Telegram updates) into use case requests.
   - Translate use case responses into HTTP responses or Telegram messages.
   - Contains FastAPI routes and Telegram bot handlers (no DB access).

4) **Infrastructure (DB, Telegram client, scheduler placeholder)**
   - Concrete implementations for repositories, unit of work, and Telegram integrations.
   - DB models / ORM mappings and migrations.
   - Background worker scheduling (placeholder now; concrete later).

### Dependency Direction Rules
- **Inward dependencies only**: Infrastructure → Interface Adapters → Use Cases → Domain.
- Domain has no dependencies on any outer layer.
- Use cases depend only on abstractions; repositories are injected.
- Interface adapters depend on use cases (not the other way around).
- Infrastructure implements interfaces defined in use cases (or core).

### Interfaces / Contracts (Minimal Signatures)
**Repositories**
- `UserRepository`
  - `get_by_telegram_id(telegram_id) -> User | None`
  - `upsert(telegram_id) -> User`
- `ReferralRepository`
  - `get_by_referred_telegram_id(telegram_id) -> Referral | None`
  - `create(referrer_telegram_id, referred_telegram_id) -> Referral`
  - `summary_for_referrer(referrer_telegram_id) -> ReferralSummary`

**Unit of Work / Transaction Boundary**
- `UnitOfWork`
  - `users: UserRepository`
  - `referrals: ReferralRepository`
  - `__aenter__ / __aexit__` or `commit()` / `rollback()` for transaction control.

**Optional Cross-Cutting**
- `TelegramNotifier`
  - `send_message(telegram_id, text) -> None` (placeholder for worker use)
- `Clock`
  - `now() -> datetime`

### Primary Use Cases (Orchestration Rules)
- **UpsertUser**
  - Input: `telegram_id`.
  - Behavior: create user if missing, return user.
- **CreateReferral (Idempotent)**
  - Input: `referrer_telegram_id`, `referred_telegram_id`.
  - Rules:
    - If `referrer_telegram_id == referred_telegram_id`: error.
    - If referral already exists for `referred_telegram_id`:
      - Return existing referral if same referrer.
      - Otherwise return conflict error.
    - Otherwise create referral (may upsert both users first).
- **GetUserStatus**
  - Input: `telegram_id`.
  - Output: user + referrer (nullable).
- **GetReferralSummary**
  - Input: `referrer_telegram_id`.
  - Output: count + last 5 referrals.

### How FastAPI + Bot Handlers Call Use Cases
- **FastAPI route** validates request → builds request model → calls use case → presenter returns HTTP response.
- **Telegram bot handler** parses update → builds use case input → calls use case → formats reply.
- Both depend on the same use case layer and do not access DB directly.

---

## F) Project Skeleton (Python Package Layout)

```
app/
  core/
    config.py             # Env + settings
    logging.py            # Logger setup, correlation IDs
    contracts.py          # Repository/UoW/Notifier/Clock interfaces
  domain/
    entities.py           # User, Referral (pure)
    value_objects.py      # TelegramId, ReferralCode (optional)
  usecases/
    upsert_user.py
    create_referral.py
    get_user_status.py
    get_referral_summary.py
    dto.py                # Request/response DTOs
  adapters/
    api/
      routes.py           # FastAPI endpoints, request parsing
      presenters.py       # HTTP response formatting
    bot/
      handlers.py         # /start, /my_status, /ref_summary
      presenters.py       # Telegram message formatting
  infrastructure/
    db/
      models.py           # ORM models / mappings
      repositories.py     # Repo implementations
      uow.py              # UnitOfWork implementation
      migrations/         # Alembic versions (or in /alembic)
    telegram/
      client.py           # Telegram API client wrapper
    scheduler/
      placeholder.py      # Worker scheduler placeholder
  api/
    app.py                # FastAPI app wiring
  bot/
    app.py                # Bot runner (polling/webhook)
  worker/
    app.py                # Background worker entrypoint (future)
tests/
  unit/
  integration/
alembic/
  env.py
  versions/
docker-compose.yml
```

### Responsibilities (Key Modules)
- **app/core/contracts.py**: defines `UserRepository`, `ReferralRepository`, `UnitOfWork`, `TelegramNotifier`, `Clock`.
- **app/domain/**: domain entities + value objects only (no infra).
- **app/usecases/**: business logic orchestrators; depend only on contracts + domain.
- **app/adapters/api/**: FastAPI routes + presenters (HTTP boundary).
- **app/adapters/bot/**: Telegram command handlers + presenters (bot boundary).
- **app/infrastructure/db/**: DB models, repository implementations, UoW.
- **app/infrastructure/telegram/**: Telegram client integration (not used in domain/usecases).
- **app/infrastructure/scheduler/**: placeholder for worker scheduling (Sprint 5 readiness).
- **app/api/app.py** and **app/bot/app.py**: application wiring / dependency injection.
- **app/worker/app.py**: future worker entrypoint to call use cases for async tasks.

### Separation of Concerns Check
- Domain + use cases contain **zero** DB/Telegram code.
- Adapters only translate input/output, not business rules.
- Infrastructure contains all external integrations.
- Worker can be added later as a new adapter without changing domain/use cases.
