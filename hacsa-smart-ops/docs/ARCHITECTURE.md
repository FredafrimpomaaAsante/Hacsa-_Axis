# Architecture and API communication

## Base URL

Local default: `http://127.0.0.1:8000`

All business routes live under `/api/v1`. System health is `GET /health` and is unauthenticated.

## Message format

- Request bodies and responses are JSON (`application/json`).
- Dates are ISO-8601 (timezone-aware).
- Money is decimal strings in JSON (for example `"1500.00"`) with currency default `GHS`.
- Errors use FastAPI’s `{ "detail": "..." }` shape. Typical codes: `401` missing/invalid token, `403` wrong role or ownership, `404` missing entity, `409` duplicate application or occupied booth.

## Auth header

After login, every protected call sends:

```http
Authorization: Bearer <access_token>
```

Clients should store the refresh token and call `POST /api/v1/auth/refresh` when access expires. Do not send the refresh token as a Bearer access token.

## Role matrix

| Endpoint group | Public | Vendor | Organizer | Admin |
| --- | --- | --- | --- | --- |
| Register / login / refresh | yes | yes | yes | yes |
| `GET /auth/me` | | own profile | own profile | own profile |
| `GET /events/public` | yes | yes | yes | yes |
| Create/update events, sessions, booths | | | own events | all |
| Submit application | | yes | | yes (acting as vendor-capable) |
| Review application | | | own events | all |
| Assign / release booth | | | own events | all |
| Initiate / confirm payment | | own assignment | allowed | allowed |
| Payment webhook | yes (shared secret should be added in production) | | | |
| Refund | | | | yes |
| Reports | | events applied to | own events | all |
| Admin users / audit / stats | | | | yes |

## Sequence: vendor onboarding to paid booth

```
Vendor                  API                     MySQL                 Organizer
  |-- POST /auth/register --------------------------> users
  |-- POST /auth/login <---- JWT pair --
  |-- GET /events/public <--- published events --
  |-- POST /applications ---------------------------> vendor_applications
                                                    notify via polling
                         <----- GET /applications --|
                         <----- POST .../review ----|
                         ---- assign booth --------> booths, booth_assignments
  |-- GET /assignments <--- active booth --
  |-- POST /payments ------------------------------> payments (pending)
  |-- POST /payments/{id}/confirm -----------------> payments (succeeded)
  |-- GET /reports/occupancy (organizer) <---------- aggregates
```

Clients do not talk to MySQL. They only talk to HTTP. Services translate HTTP into row changes and write `audit_logs` in the same commit.

## Sequence: simulated payment gateway

```
Vendor app                 This API                    Gateway (simulated)
  | POST /payments           | create pending + reference
  |                          | (production: create PSP charge here)
  | POST /payments/{id}/confirm
  |                          | mark succeeded/failed
  |                          | <--- alternative: POST /payments/webhooks/gateway
```

In production, the confirm route might disappear and only the webhook would settle the row. Both paths update the same `status` field so reporting stays consistent.

## Resource catalog

### Authentication — `/api/v1/auth`

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/register` | no | Create organizer or vendor |
| POST | `/login` | no | Issue tokens |
| POST | `/refresh` | refresh body | Rotate tokens |
| GET | `/me` | Bearer | Current user |

Register body example:

```json
{
  "email": "organizer@hacsa10.example.com",
  "password": "Organizer123!",
  "full_name": "Ama Mensah",
  "role": "organizer",
  "organization_name": "HACSA@10 Organizing Committee"
}
```

Vendor register uses `"role": "vendor"` and `business_name`.

### Events and sessions — `/api/v1/events`

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/public` | Catalog of published/live events |
| GET | `/` | Role-filtered event list |
| POST | `/` | Create event |
| GET | `/{event_id}` | Event detail |
| PATCH | `/{event_id}` | Update including `status` |
| GET | `/{event_id}/sessions` | Agenda |
| POST | `/{event_id}/sessions` | Add session |
| PATCH | `/sessions/{session_id}` | Update session |
| GET | `/{event_id}/booths` | Booth inventory |
| POST | `/{event_id}/booths` | Add booth |

Event statuses: `draft`, `published`, `live`, `completed`, `cancelled`. Vendors can apply only when the event is `published` or `live`.

### Applications — `/api/v1/applications`

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/` | Vendor applies (`event_id`, `products`, optional message/size) |
| GET | `/` | Vendor: own apps. Organizer: apps on owned events. Query `event_id` optional |
| POST | `/{id}/review` | Organizer sets status; optional `booth_id` |

Review body:

```json
{
  "status": "approved",
  "review_notes": "Good fit for zone A",
  "booth_id": 1
}
```

### Assignments — `/api/v1`

| Method | Path | Purpose |
| --- | --- | --- |
| PATCH | `/booths/{booth_id}` | Update fee/zone/status |
| POST | `/assignments` | Assign booth to vendor |
| GET | `/assignments` | List (scoped by role, optional `event_id`) |
| POST | `/assignments/{id}/release` | Free the booth |

### Payments — `/api/v1/payments`

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/` | Create pending transaction |
| GET | `/` | List (scoped). Query `event_id` |
| POST | `/{id}/confirm` | `{ "succeed": true, "provider_ref": "optional" }` |
| POST | `/webhooks/gateway` | `{ "reference": "HACSA-…", "status": "succeeded" }` |
| POST | `/{id}/refund` | Admin refund |

Statuses: `pending`, `succeeded`, `failed`, `refunded`. Methods: `card`, `bank_transfer`, `mobile_money`, `cash`.

### Reports — `/api/v1/reports`

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/events/{event_id}/summary` | Sessions, approved vendors, occupancy, revenue, funnel |
| GET | `/occupancy` | Booth fill rate per visible event |
| GET | `/revenue` | Sums by payment status |
| GET | `/applications` | Counts by application status |

### Administration — `/api/v1/admin`

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/users` | All accounts |
| PATCH | `/users/{id}` | `{ "is_active": false }` or `{ "role": "organizer" }` |
| GET | `/audit-logs` | Recent actions (`limit` up to 500) |
| GET | `/stats` | Totals for users, events, applications, payments |

## How clients should compose calls

A frontend is expected to:

1. Login and keep tokens in memory or secure storage.
2. Attach the access token on every XHR/fetch.
3. Use `/auth/me` once to branch UI (organizer console vs vendor console vs admin).
4. Poll or refresh lists after mutations (applications after review, booths after assign).
5. For payments, create then confirm, then reload reports.

There is no WebSocket layer. Near-real-time UX is HTTP polling or a later notification service.

## CORS

`CORS_ORIGINS` in `.env` is a comma-separated list (for example `http://localhost:5173`). Browsers hosting a Vite/React app must be listed there.

## OpenAPI as the live contract

`GET /openapi.json` is the machine-readable contract. If a client generator is used, point it at that URL after the server is running. Human-oriented try-it-out is `/docs`.
