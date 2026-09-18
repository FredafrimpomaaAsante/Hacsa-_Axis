from decimal import Decimal

from pydantic import BaseModel


class OccupancyReport(BaseModel):
    event_id: int
    event_name: str
    total_booths: int
    assigned_booths: int
    available_booths: int
    occupancy_rate: float


class RevenueReport(BaseModel):
    event_id: int
    event_name: str
    succeeded_amount: Decimal
    pending_amount: Decimal
    refunded_amount: Decimal
    transaction_count: int


class ApplicationFunnel(BaseModel):
    event_id: int
    submitted: int
    under_review: int
    approved: int
    rejected: int


class EventSummary(BaseModel):
    event_id: int
    event_name: str
    sessions: int
    vendors_approved: int
    occupancy: OccupancyReport
    revenue: RevenueReport
    applications: ApplicationFunnel
