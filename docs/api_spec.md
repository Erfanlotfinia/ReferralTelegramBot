# Referral API Spec

## Common
- Base URL: `/`
- Content-Type: `application/json`
- Idempotency: referral creation returns **201** when created, **200** when the same referrer already referred the same user, and **409** when the referred user already has a different referrer.

## Models (Pydantic-style)

```python
class UserUpsertRequest(BaseModel):
    telegram_id: int

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    created_at: datetime

class ReferralCreateRequest(BaseModel):
    referrer_telegram_id: int
    referred_telegram_id: int

class ReferralResponse(BaseModel):
    id: int
    referrer_telegram_id: int
    referred_telegram_id: int
    created_at: datetime

class UserStatusResponse(BaseModel):
    telegram_id: int
    referred_by: int | None
    referral_count: int

class ReferralSummaryItem(BaseModel):
    referred_telegram_id: int
    created_at: datetime

class ReferralSummaryResponse(BaseModel):
    referrer_telegram_id: int
    count: int
    last_5_referrals: list[ReferralSummaryItem]
```

## Endpoints

### 1) POST `/users/upsert`
**Request**
```json
{
  "telegram_id": 123456789
}
```

**Response 200**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors**
- 400: invalid `telegram_id` (non-positive)

---

### 2) POST `/referrals`
**Request**
```json
{
  "referrer_telegram_id": 111,
  "referred_telegram_id": 222
}
```

**Response 201 (created)**
```json
{
  "id": 10,
  "referrer_telegram_id": 111,
  "referred_telegram_id": 222,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Response 200 (idempotent)**
```json
{
  "id": 10,
  "referrer_telegram_id": 111,
  "referred_telegram_id": 222,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors**
- 400: invalid ids or self-referral
- 409: referred user already has a different referrer

---

### 3) GET `/users/{telegram_id}/status`
**Response 200**
```json
{
  "telegram_id": 222,
  "referred_by": 111,
  "referral_count": 3
}
```

**Errors**
- 404: user not found

---

### 4) GET `/referrals/{referrer_telegram_id}/summary`
**Response 200**
```json
{
  "referrer_telegram_id": 111,
  "count": 3,
  "last_5_referrals": [
    {
      "referred_telegram_id": 222,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```
