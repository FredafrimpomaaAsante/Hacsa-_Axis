import asyncio
import json
from uuid import uuid4
from urllib.parse import urlsplit

import pytest
from fastapi import HTTPException

from app.email_service import send_registration_confirmation_email
from app.main import app, public_config
from app.models.user import RoleEnum, User
from app.models.networking import ConnectionStatusEnum
from app.models.enums import AlertLevel, AlertType
from app.models.safety import SafetyAlert
from app.routers.auth import login, register
from app.routers.badges import verify_badge
from app.services import send_connection_request, respond_to_connection, get_notifications_for_user, create_user
from app.schemas.user import UserCreate, UserLogin
from app.connections import SessionLocal
from app.utils import create_access_token


async def asgi_request(method, url, headers=None, body=b""):
    parsed_url = urlsplit(url)
    request_sent = False
    messages = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": parsed_url.path,
        "raw_path": parsed_url.path.encode(),
        "query_string": parsed_url.query.encode(),
        "root_path": "",
        "headers": [
            (name.lower().encode(), value.encode())
            for name, value in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    response_start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return {"status_code": response_start["status"], "json": json.loads(response_body or b"null")}


def test_registration_email_uses_smtp(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port):
            captured["host"] = host
            captured["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            captured["tls"] = True

        def login(self, username, password):
            captured["login"] = (username, password)

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr("app.email_service.settings.SMTP_HOST", "smtp.example.com", raising=False)
    monkeypatch.setattr("app.email_service.settings.SMTP_PORT", "587", raising=False)
    monkeypatch.setattr("app.email_service.settings.SMTP_USERNAME", "demo@example.com", raising=False)
    monkeypatch.setattr("app.email_service.settings.SMTP_PASSWORD", "secret", raising=False)
    monkeypatch.setattr("app.email_service.settings.SMTP_FROM_EMAIL", "no-reply@hacsaxis.com", raising=False)
    monkeypatch.setattr("app.email_service.settings.SMTP_USE_TLS", True, raising=False)
    monkeypatch.setattr("app.email_service.smtplib.SMTP", FakeSMTP)

    result = send_registration_confirmation_email(
        "user@example.com",
        "Ada Mensah",
        "Sankofa Summit 2026",
        "summit-2026",
    )

    assert result is True
    assert captured["host"] == "smtp.example.com"
    assert captured["message"]["To"] == "user@example.com"
    assert "Sankofa Summit 2026" in captured["message"].get_content()
    assert captured["message"]["Subject"] == "Registration confirmed for Sankofa Summit 2026"


def test_badge_verification_shows_no_event_registered_when_missing():
    with SessionLocal() as db:
        user = User(
            full_name="No Event User",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        badge = verify_badge(user.person_id, db)

        assert badge["full_name"] == "No Event User"
        assert badge["registered"] is False
        assert badge["event_id"] is None
        assert badge["event_name"] == "No event registered"


def test_connection_request_creates_notification_and_can_be_accepted_or_declined():
    with SessionLocal() as db:
        requester = User(
            full_name="Requester User",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        recipient = User(
            full_name="Recipient User",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        db.add_all([requester, recipient])
        db.commit()
        db.refresh(requester)
        db.refresh(recipient)

        connection = send_connection_request(db, requester.id, recipient.id)

        notifications = get_notifications_for_user(db, recipient.id)
        assert any(
            n.title == "New connection request" and "connect with you" in n.message.lower()
            for n in notifications
        )
        assert connection.status == ConnectionStatusEnum.pending

        respond_to_connection(db, connection, accept=True)
        assert connection.status == ConnectionStatusEnum.accepted

        declined = send_connection_request(db, recipient.id, requester.id)
        respond_to_connection(db, declined, accept=False)
        assert declined.status == ConnectionStatusEnum.declined


def test_user_can_be_marked_as_not_open_to_connect():
    with SessionLocal() as db:
        user = create_user(
            db,
            UserCreate(
                full_name="Quiet User",
                email=f"{uuid4().hex}@example.com",
                password="secret123",
                role=RoleEnum.speaker,
                is_open_to_connect=False,
            ),
        )

        assert user.is_open_to_connect is False


def test_vendor_can_register_and_sign_in():
    email = f"{uuid4().hex}@example.com"
    password = "vendor-secret-123"

    with SessionLocal() as db:
        registration = register(
            UserCreate(
                full_name="Vendor User",
                email=email,
                password=password,
                role=RoleEnum.vendor,
            ),
            db,
        )
        signed_in = login(UserLogin(email=email, password=password), db)

        assert registration.user.role == RoleEnum.vendor
        assert signed_in.user.role == RoleEnum.vendor
        assert signed_in.access_token


def test_organiser_signup_requires_invitation_code(monkeypatch):
    monkeypatch.setattr("app.routers.auth.settings.ORGANISER_SIGNUP_CODE", "", raising=False)
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as error:
            register(
                UserCreate(
                    full_name="Unprovisioned Organiser",
                    email=f"{uuid4().hex}@example.com",
                    password="organiser-secret-123",
                    role=RoleEnum.organiser,
                ),
                db,
            )

        assert error.value.status_code == 403


def test_organiser_signup_rejects_incorrect_invitation(monkeypatch):
    monkeypatch.setattr(
        "app.routers.auth.settings.ORGANISER_SIGNUP_CODE",
        "configured-invitation",
        raising=False,
    )
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as error:
            register(
                UserCreate(
                    full_name="Invalid Invite Organiser",
                    email=f"{uuid4().hex}@example.com",
                    password="organiser-secret-123",
                    role=RoleEnum.organiser,
                    organiser_code="wrong-invitation",
                ),
                db,
            )

        assert error.value.status_code == 403


def test_organiser_can_register_and_sign_in_with_invitation(monkeypatch):
    invitation_code = "hacsa-organiser-invite-test"
    monkeypatch.setattr(
        "app.routers.auth.settings.ORGANISER_SIGNUP_CODE",
        invitation_code,
        raising=False,
    )
    email = f"{uuid4().hex}@example.com"
    password = "organiser-secret-123"

    with SessionLocal() as db:
        registration = register(
            UserCreate(
                full_name="Invited Organiser",
                email=email,
                password=password,
                role=RoleEnum.organiser,
                organiser_code=invitation_code,
            ),
            db,
        )
        signed_in = login(UserLogin(email=email, password=password), db)

        assert registration.user.role == RoleEnum.organiser
        assert signed_in.user.role == RoleEnum.organiser


def test_activity_feed_includes_authenticated_actions_for_organisers_and_operations():
    with SessionLocal() as db:
        requester = User(
            full_name="Activity Requester",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        recipient = User(
            full_name="Activity Recipient",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        organiser = User(
            full_name="Activity Organiser",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.organiser,
        )
        operations = User(
            full_name="Activity Operations",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.ops_lead,
        )
        db.add_all([requester, recipient, organiser, operations])
        db.commit()
        db.refresh(requester)
        db.refresh(recipient)
        db.refresh(organiser)
        db.refresh(operations)
        requester_token = create_access_token({"sub": requester.person_id, "person_id": requester.person_id})
        organiser_token = create_access_token({"sub": organiser.person_id, "person_id": organiser.person_id})
        operations_token = create_access_token({"sub": operations.person_id, "person_id": operations.person_id})

    action_response = asyncio.run(asgi_request(
        "POST",
        f"/network/connect/{recipient.id}",
        headers={"Authorization": f"Bearer {requester_token}"},
    ))
    assert action_response["status_code"] == 201

    organiser_response = asyncio.run(asgi_request(
        "GET",
        "/api/v1/audit/activity?limit=50",
        headers={"Authorization": f"Bearer {organiser_token}"},
    ))
    operations_response = asyncio.run(asgi_request(
        "GET",
        "/api/v1/audit/activity?limit=50",
        headers={"Authorization": f"Bearer {operations_token}"},
    ))

    assert organiser_response["status_code"] == 200
    assert operations_response["status_code"] == 200
    assert any(
        entry["actor_id"] == str(requester.id)
        and "Activity Requester" in entry["detail"]
        and "/network/connect/{user_id}" in entry["detail"]
        for entry in organiser_response["json"]
    )
    assert any(
        entry["actor_id"] == str(requester.id)
        for entry in operations_response["json"]
    )


def test_public_config_exposes_event_center_for_operations_map():
    config = public_config()
    center = config["event_center"]

    assert center["name"]
    assert center["location"] == "Accra, Ghana"
    assert isinstance(center["latitude"], float)
    assert isinstance(center["longitude"], float)
    assert center["coordinates_approximate"] is True


def test_attendee_can_report_location_tagged_help_request_for_operations():
    event_id = f"help-{uuid4().hex}"
    with SessionLocal() as db:
        attendee = User(
            full_name="Help Request Attendee",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        operations = User(
            full_name="Help Request Operations",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.ops_lead,
        )
        db.add_all([attendee, operations])
        db.commit()
        db.refresh(attendee)
        db.refresh(operations)
        attendee_token = create_access_token({"sub": attendee.person_id, "person_id": attendee.person_id})
        operations_token = create_access_token({"sub": operations.person_id, "person_id": operations.person_id})

    report_response = asyncio.run(asgi_request(
        "POST",
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {attendee_token}", "Content-Type": "application/json"},
        body=json.dumps({
            "event_id": event_id,
            "title": "Venue navigation",
            "location": "Exhibition Hall",
            "description": "Please help me find the accessible entrance.",
            "severity": "low",
        }).encode(),
    ))
    incidents_response = asyncio.run(asgi_request(
        "GET",
        f"/api/v1/incidents/?event_id={event_id}",
        headers={"Authorization": f"Bearer {operations_token}"},
    ))

    assert report_response["status_code"] == 200
    assert incidents_response["status_code"] == 200
    assert incidents_response["json"][0]["location"] == "Exhibition Hall"
    assert incidents_response["json"][0]["status"] == "open"


def test_vendor_can_report_location_tagged_help_request():
    event_id = f"vendor-help-{uuid4().hex}"
    with SessionLocal() as db:
        vendor = User(
            full_name="Vendor Help Requester",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.vendor,
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        vendor_token = create_access_token({"sub": vendor.person_id, "person_id": vendor.person_id})

    response = asyncio.run(asgi_request(
        "POST",
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {vendor_token}", "Content-Type": "application/json"},
        body=json.dumps({
            "event_id": event_id,
            "title": "Booth/setup issue",
            "location": "Loading Bay",
            "description": "Our setup delivery needs assistance.",
            "severity": "low",
        }).encode(),
    ))

    assert response["status_code"] == 200
    assert response["json"]["location"] == "Loading Bay"


def test_medical_report_escalates_and_resolving_incident_clears_alert():
    event_id = f"medical-{uuid4().hex}"
    with SessionLocal() as db:
        attendee = User(
            full_name="Medical Help Requester",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        operations = User(
            full_name="Medical Operations",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.ops_lead,
        )
        db.add_all([attendee, operations])
        db.commit()
        db.refresh(attendee)
        db.refresh(operations)
        attendee_token = create_access_token({"sub": attendee.person_id, "person_id": attendee.person_id})
        operations_token = create_access_token({"sub": operations.person_id, "person_id": operations.person_id})

    response = asyncio.run(asgi_request(
        "POST",
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {attendee_token}", "Content-Type": "application/json"},
        body=json.dumps({
            "event_id": event_id,
            "title": "Medical emergency",
            "location": "Main Entrance",
            "description": "A guest needs urgent medical help.",
            "severity": "low",
        }).encode(),
    ))

    assert response["status_code"] == 200
    incident = response["json"]
    assert incident["severity"] == "critical"

    with SessionLocal() as db:
        alert = db.query(SafetyAlert).filter(SafetyAlert.incident_id == incident["id"]).one()
        assert alert.alert_type == AlertType.MEDICAL
        assert alert.level == AlertLevel.CRITICAL
        assert alert.resolved is False

    resolved = asyncio.run(asgi_request(
        "PATCH",
        f"/api/v1/incidents/{incident['id']}/status",
        headers={"Authorization": f"Bearer {operations_token}", "Content-Type": "application/json"},
        body=json.dumps({"status": "resolved"}).encode(),
    ))
    assert resolved["status_code"] == 200

    with SessionLocal() as db:
        alert = db.query(SafetyAlert).filter(SafetyAlert.incident_id == incident["id"]).one()
        assert alert.resolved is True


def test_high_priority_report_creates_elevated_safety_alert():
    event_id = f"priority-{uuid4().hex}"
    with SessionLocal() as db:
        attendee = User(
            full_name="Priority Help Requester",
            email=f"{uuid4().hex}@example.com",
            hashed_password="unused",
            role=RoleEnum.participant,
        )
        db.add(attendee)
        db.commit()
        db.refresh(attendee)
        token = create_access_token({"sub": attendee.person_id, "person_id": attendee.person_id})

    response = asyncio.run(asgi_request(
        "POST",
        "/api/v1/incidents/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        body=json.dumps({
            "event_id": event_id,
            "title": "High-priority issue",
            "location": "Exhibition Hall",
            "description": "An urgent accessibility issue needs help.",
            "severity": "high",
        }).encode(),
    ))

    assert response["status_code"] == 200
    with SessionLocal() as db:
        alert = db.query(SafetyAlert).filter(
            SafetyAlert.incident_id == response["json"]["id"]
        ).one()
        assert alert.alert_type == AlertType.INCIDENT
        assert alert.level == AlertLevel.ELEVATED
        assert alert.resolved is False
