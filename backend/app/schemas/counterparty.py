from uuid import UUID

from pydantic import BaseModel, Field


class CounterpartyProfile(BaseModel):
    id: UUID
    first_name: str
    last_initial: str
    self_reported_skill_label: str | None = None
    confirmed_skill_label: str | None = None
    is_act_manager: bool = False
    is_booking_coordinator: bool = False
    manager_verified: bool = False
    manager_self_report_labels: list[str] = Field(default_factory=list)
