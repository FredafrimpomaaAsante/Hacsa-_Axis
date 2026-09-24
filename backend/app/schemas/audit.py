from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditAction


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: str
    actor_role: str
    action: AuditAction
    entity_type: str
    entity_id: str | None
    detail: str | None
    ip_address: str | None
    created_at: datetime