# HACSA Axis

One event platform. The original participant, organiser, vendor, and operations pages are kept and served together, connected to a single FastAPI backend.

## Run everything from one place

```bash
chmod +x start.sh
./start.sh
```

That script creates the virtual environment, installs dependencies, creates the database, runs migrations, inserts demo users and programme data, then starts the app.

Open http://127.0.0.1:8000

## Workspaces

Sign in on the original HACSA Axis login screen. Role decides which of their pages you enter:

| Role | Pages |
| --- | --- |
| Participant / speaker | `/portal/` — overview, schedule, badge, networking, polls, speaker studio |
| Organiser | `/organiser/` — dashboard, events, participants, registrations, vendors, submissions, analytics, settings |
| Vendor | `/vendor/` — vendor portal |
| Operations | `/ops/` — command center, safety, analytics |

Demo accounts (password `Axis2026!`):

- attendee@hacsa.org
- speaker@hacsa.org
- organiser@hacsa.org
- ops@hacsa.org
