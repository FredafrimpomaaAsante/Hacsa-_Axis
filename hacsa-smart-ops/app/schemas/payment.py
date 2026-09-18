from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    event_id: int
    assignment_id: int | None = None
    amount: Decimal = Field(gt=0)
    currency: str = "GHS"
    method: PaymentMethod = PaymentMethod.CARD
    description: str | None = None


class PaymentConfirm(BaseModel):
    succeed: bool = True
    provider_ref: str | None = None


class PaymentWebhook(BaseModel):
    reference: str
    status: PaymentStatus
    provider_ref: str | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payer_id: int
    event_id: int
    assignment_id: int | None
    amount: Decimal
    currency: str
    method: PaymentMethod
    status: PaymentStatus
    reference: str
    provider_ref: str | None
    description: str | None
    created_at: datetime
    settled_at: datetime | None
