# Backend Developer 1 — Participants & Speakers

FastAPI service covering:

- User authentication and role identification
- Participant and speaker profiles
- Unique speaker IDs and secure authentication
- Speaker session assignments
- Session, venue, and schedule APIs
- Schedule-change notifications
- Networking, polls, Q&A, and feedback


## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# open .env and set SECRET_KEY (the app refuses to start without it)
# leave DATABASE_URL blank to use SQLite, or point it at Postgres/MySQL

uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs** for interactive Swagger docs.

## Project structure

```
app/
├── main.py           # FastAPI app, router registration, table creation
├── config.py          # env-based settings (secret key, token expiry)
├── connections.py       # SQLAlchemy engine/session — DB connection setup
├── models/               # SQLAlchemy ORM tables
│   ├── user.py               # User, RoleEnum, ParticipantProfile, SpeakerProfile
│   ├── schedule.py             # Venue, Session, SessionSpeaker, SessionInterest
│   ├── notification.py          # Notification
│   ├── networking.py             # NetworkConnection
│   └── engagement.py              # Poll, PollOption, PollVote, Question, Feedback
├── schemas/               # Pydantic request/response models (mirrors models/)
├── services.py             # ALL business logic / DB queries, grouped by domain
├── utils.py                 # password hashing, JWT, get_current_user, require_roles
└── routers/                  # API route handlers per domain
    ├── auth.py
    ├── profiles.py
    ├── schedule.py
    ├── notifications.py
    ├── networking.py
    └── engagement.py
```

## Roles

`participant` · `speaker` · `organiser` (embedded in the JWT on login and
enforced per-route via `require_roles(...)` in `utils.py`).

Registering as a `speaker` auto-generates a unique `speaker_code` (e.g.
`SPK-4F91A2C0`); registering as a `participant` auto-creates an empty
participant profile ready to fill in.

## Endpoints

### Authentication & Roles
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create an account with a role |
| POST | `/auth/login` | — | Get a JWT (role embedded) |

### Participant & Speaker Profiles
| Method | Path | Auth | Description |
|---|---|---|---|
| GET/PUT | `/participants/me` | participant | Own participant profile |
| GET | `/speakers` | — | Public speaker directory |
| GET/PUT | `/speakers/me` | speaker | Own speaker profile |
| GET | `/speakers/{speaker_code}` | — | Look up a speaker by their unique ID |

### Session, Venue & Schedule
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/venues` | — | List venues |
| GET | `/venues/{id}` | — | Venue detail |
| POST | `/venues` | organiser | Add a venue |
| GET | `/schedule/sessions` | — | List sessions |
| GET | `/schedule/sessions/{id}` | — | Session detail |
| POST | `/schedule/sessions` | organiser | Create a session |
| PATCH | `/schedule/sessions/{id}` | organiser | Reschedule/cancel — **auto-notifies** |
| POST | `/schedule/sessions/{id}/speakers/{speaker_code}` | organiser | Assign a speaker |
| GET | `/schedule/sessions/{id}/speakers` | — | Speakers assigned to a session |
| GET | `/speakers/{speaker_code}/sessions` | — | A speaker's assigned sessions |
| POST | `/schedule/sessions/{id}/interest` | user | Follow a session for change alerts |
| GET | `/users/me/interests` | user | Sessions you're following |

### Notifications
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/notifications` | user | List own notifications (`?unread_only=true`) |
| PATCH | `/notifications/{id}/read` | user | Mark one as read |

### Networking
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/network/directory` | user | Browse other attendees |
| POST | `/network/connect/{user_id}` | user | Send a connection request |
| PATCH | `/network/connections/{id}` | user | Accept/decline a request |
| GET | `/network/connections` | user | List your connections (`?status=`) |

### Polls, Q&A & Feedback
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/engagement/polls` | speaker/organiser | Create a poll with options |
| GET | `/engagement/polls` | — | List polls (`?session_id=`) |
| POST | `/engagement/polls/{id}/vote/{option_id}` | user | Vote (one per poll) |
| GET | `/engagement/polls/{id}/results` | — | Live tally |
| POST | `/engagement/sessions/{id}/questions` | user | Ask a question |
| GET | `/engagement/sessions/{id}/questions` | — | List, sorted by upvotes |
| POST | `/engagement/questions/{id}/upvote` | user | Upvote a question |
| PATCH | `/engagement/questions/{id}/answer` | speaker/organiser | Mark answered |
| POST | `/engagement/sessions/{id}/feedback` | user | Submit/update feedback (1–5) |
| GET | `/engagement/sessions/{id}/feedback/summary` | speaker/organiser | Average rating |

## How schedule-change notifications work

`PATCH /schedule/sessions/{id}` compares the incoming fields against the
session's current values. If `start_time`, `end_time`, `venue_id`, or
`status` actually changed, `notify_schedule_change()` in `services.py`
builds a message from the session's real data (never a fixed string) and
creates a `Notification` for every speaker assigned to that session and
every participant who called `POST .../interest` on it.

## "Don't hard code" — what that means here

- `connections.py` reads `DATABASE_URL` from the environment; no host,
  user, or password is written into the code. Swap SQLite for
  Postgres/MySQL by setting one variable.
- `config.py` reads `SECRET_KEY` from the environment and **raises an
  error on startup** if it isn't set, rather than silently using a fixed
  fallback secret.
- Speaker IDs are generated with `generate_speaker_code()` (UUID-based) —
  never a literal string.
- Notification titles/messages are built from the session's actual title,
  time, and status at the moment of the change.
- No endpoint returns stubbed/mock data — everything is a real DB query.

