# How this backend was built

This document records the design choices for the HACSA@10 **Organizers & Vendors** backend and how the pieces fit together at runtime.

## Scope source

The work follows the Backend Developer 2 slide:

- Organizer and vendor authentication
- Vendor applications and approvals
- Booth assignments
- Payment and transaction APIs
- Event and session management
- Role-based access controls
- Administration and reporting services

The product name is **HACSA AXIS**. This service is the operations API for staff who run events and for vendors who occupy booths. It is intentionally a JSON REST API so a future web or mobile client can sit in front of it without changing domain rules.

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| HTTP API | FastAPI | Typed request/response models, automatic OpenAPI, dependency injection for auth |
| Validation | Pydantic v2 | Shared shapes between HTTP and services |
| ORM | SQLAlchemy 2.x mapped classes | Explicit models that map cleanly onto MySQL |
| Database | MySQL 8 via PyMySQL | Requested datastore; `pool_pre_ping` survives idle connections |
| Migrations | Alembic | Versioned schema matching the ORM tables |
| Auth | JWT access + refresh, bcrypt passwords | Stateless API auth with short-lived access tokens |
| Config | `pydantic-settings` + `.env` | Local MySQL URL without hard-coding secrets in code |

Docker is not included. The app expects a MySQL instance already running on the machine.

## Layout

```
app/
  main.py                 FastAPI app, CORS, lifespan (tables + admin seed)
  core/                   Settings, JWT/password helpers, auth dependencies, ownership checks
  db/                     Engine, session, declarative Base
  models/                 Users, events, sessions, applications, booths, payments, audit
  schemas/                Request and response DTOs
  services/               Business rules (the only place status machines live)
  api/v1/                 Thin HTTP adapters
scripts/seed.py           Demo organizer/vendor/event data
alembic/                  Schema migration
docs/                     This file and architecture
tests/                    End-to-end flow against SQLite
```

HTTP handlers do not embed SQL. They parse a payload, resolve the current user, call a service, and return a schema. That keeps OpenAPI documentation aligned with real rules and makes reporting queries reusable.

## Domain model

```
User (admin | organizer | vendor)
  └── Event (owned by organizer)
        ├── EventSession
        ├── Booth
        │     └── BoothAssignment → Vendor User
        ├── VendorApplication → Vendor User
        └── Payment → payer User, optional assignment
AuditLog (who did what to which entity)
```

Important constraints:

- One vendor application per event (`uq_vendor_event_application`).
- One booth code per event (`uq_event_booth_code`).
- A booth cannot receive a second **active** assignment.
- Approving an application can optionally assign a booth in the same request.
- Vendors may only pay against their own assignment.
- Only admins can refund succeeded payments or change other users’ roles.

## Authentication and RBAC

1. `POST /api/v1/auth/register` creates an organizer or vendor. Admin self-registration is rejected.
2. `POST /api/v1/auth/login` verifies bcrypt and returns access + refresh JWTs. Claims include `sub` (user id), `role`, and `typ`.
3. Protected routes use `HTTPBearer`. `get_current_user` decodes the **access** token and loads an active user.
4. `require_roles(...)` is a FastAPI dependency. Examples:
   - Organizer routes: `admin` or `organizer`
   - Vendor apply: `admin` or `vendor`
   - Admin console: `admin` only
5. Ownership is a second gate. An organizer may only mutate events they own; admins bypass that check.

Refresh tokens (`typ=refresh`) cannot be used as access tokens.

On startup, if no row exists for `SEED_ADMIN_EMAIL`, the lifespan hook creates an admin so the platform is usable before any UI exists.

## How a request moves through the stack

```
Client
  → CORS middleware
  → FastAPI route (path + JSON schema)
  → Auth dependency (JWT → User)
  → Role dependency
  → Service (rules, queries, audit log)
  → SQLAlchemy Session
  → MySQL
  → Response schema
```

`get_db` opens a session per request, **commits** if the handler returns, and **rolls back** on exceptions. That means a failed booth assignment during application review does not leave a half-approved application.

## Feature flows

### Events and sessions

Organizers create draft events, add sessions (agenda items), add booth inventory, then set `status` to `published` or `live`. Public listing (`GET /api/v1/events/public`) only returns published/live events. Vendors see the same published set. Organizers see only their events; admins see all.

### Applications and approvals

Vendors submit products and optional booth-size preference. Organizers list applications for their events and `POST /applications/{id}/review` with `under_review`, `approved`, or `rejected`. If `booth_id` is sent with `approved`, the assignment service runs in the same transaction.

### Booths

Organizers CRUD booths on an event. `POST /assignments` links an approved vendor to a free booth and marks the booth `assigned`. `POST /assignments/{id}/release` frees the booth again.

### Payments

This environment has no card processor, so the API **simulates** a gateway:

1. `POST /payments` creates `pending` with a unique `HACSA-…` reference.
2. `POST /payments/{id}/confirm` is the client-side capture (success or failure).
3. `POST /payments/webhooks/gateway` is the server-to-server path a real PSP would call.
4. `POST /payments/{id}/refund` is admin-only.

A production swap would keep the same `Payment` row and replace confirm/webhook internals with Paystack, Stripe, or a bank API. Reports already key off `Payment.status`, so they would not need redesign.

### Administration and reporting

Admins can list users, disable accounts, read audit logs, and see platform counts. Reports aggregate occupancy, revenue by payment status, and the application funnel. Organizers get those aggregates for events they own; vendors only see events they applied to.

## Local MySQL vs tests

Production-shaped development uses `DATABASE_URL=mysql+pymysql://...`. Pytest sets `DATABASE_URL` to SQLite in memory **before** importing the app so the same models run without MySQL. Enum columns are stored as strings (`native_enum=False`) so MySQL and SQLite stay compatible.

## What “fully functioning” means here

The API is complete for the organizer/vendor slice: register/login, CRUD of events and sessions, apply/review, assign/release booths, initiate/confirm/refund payments, RBAC, audit, and reports. It does not include attendee ticketing, push notifications, or a real payment provider. Those would be additional services speaking to the same events and users tables.
