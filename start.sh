#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
cd "$BACKEND"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

export PYTHONPATH="$BACKEND"
python - <<'PY'
from alembic import command
from alembic.config import Config

from app.connections import Base, SessionLocal, engine
from app import models  # noqa: F401
from app.seed import seed_demo

Base.metadata.create_all(bind=engine)
command.upgrade(Config("alembic.ini"), "head")
with SessionLocal() as db:
    seed_demo(db)
print("Database ready. Demo users: attendee@hacsa.org, speaker@hacsa.org, organiser@hacsa.org, ops@hacsa.org / Axis2026!")
PY

echo "Starting HACSA Axis at http://127.0.0.1:8000"
exec python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
