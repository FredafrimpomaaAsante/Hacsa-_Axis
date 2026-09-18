from datetime import datetime, timedelta, timezone


def _register(client, email: str, role: str, extra: dict | None = None):
    body = {
        "email": email,
        "password": "Password123!",
        "full_name": email.split("@")[0],
        "role": role,
    }
    if extra:
        body.update(extra)
    response = client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _login(client, email: str, password: str = "Password123!"):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_vendor_cannot_create_event(client):
    _register(client, "vendor1@example.com", "vendor", {"business_name": "Test Co"})
    token = _login(client, "vendor1@example.com")
    now = datetime.now(timezone.utc)
    response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Blocked",
            "venue": "Accra",
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 403


def test_full_vendor_flow(client):
    _register(client, "org@example.com", "organizer", {"organization_name": "HACSA Ops"})
    _register(client, "ven@example.com", "vendor", {"business_name": "Crafts"})
    org = _login(client, "org@example.com")
    ven = _login(client, "ven@example.com")
    now = datetime.now(timezone.utc)
    event = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {org}"},
        json={
            "name": "HACSA@10 Expo",
            "venue": "AICC",
            "start_at": (now + timedelta(days=10)).isoformat(),
            "end_at": (now + timedelta(days=12)).isoformat(),
            "status": "published",
        },
    )
    assert event.status_code == 201, event.text
    event_id = event.json()["id"]

    booth = client.post(
        f"/api/v1/events/{event_id}/booths",
        headers={"Authorization": f"Bearer {org}"},
        json={"code": "B1", "fee": "500.00", "size": "3x3"},
    )
    assert booth.status_code == 201, booth.text
    booth_id = booth.json()["id"]

    application = client.post(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {ven}"},
        json={"event_id": event_id, "products": "Apparel"},
    )
    assert application.status_code == 201, application.text

    review = client.post(
        f"/api/v1/applications/{application.json()['id']}/review",
        headers={"Authorization": f"Bearer {org}"},
        json={"status": "approved", "booth_id": booth_id, "review_notes": "Approved"},
    )
    assert review.status_code == 200, review.text

    assignments = client.get("/api/v1/assignments", headers={"Authorization": f"Bearer {ven}"})
    assert assignments.status_code == 200
    assignment_id = assignments.json()[0]["id"]

    payment = client.post(
        "/api/v1/payments",
        headers={"Authorization": f"Bearer {ven}"},
        json={"event_id": event_id, "assignment_id": assignment_id, "amount": "500.00"},
    )
    assert payment.status_code == 201, payment.text
    confirmed = client.post(
        f"/api/v1/payments/{payment.json()['id']}/confirm",
        headers={"Authorization": f"Bearer {ven}"},
        json={"succeed": True},
    )
    assert confirmed.json()["status"] == "succeeded"

    summary = client.get(
        f"/api/v1/reports/events/{event_id}/summary",
        headers={"Authorization": f"Bearer {org}"},
    )
    assert summary.status_code == 200, summary.text
    assert summary.json()["occupancy"]["assigned_booths"] == 1
    assert float(summary.json()["revenue"]["succeeded_amount"]) == 500.0
