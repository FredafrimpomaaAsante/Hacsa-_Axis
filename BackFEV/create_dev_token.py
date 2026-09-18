from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings


payload = {
    "sub": "ops-user-001",
    "role": "ops_lead",
    "exp": datetime.now(timezone.utc) + timedelta(hours=24),
}

token = jwt.encode(
    payload,
    settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)

print(token)
