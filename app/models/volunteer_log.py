from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class VolunteerLog(SQLModel, table=True):
    # Phase 5 workflow 1: complete the model fields from the wireframe.
    log_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    event_name: str
    hours: float
    event_date: date
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    proof: str
    additional_info: Optional[str] = Field(default=None)
    status: str = Field(default="pending")
    rejection_reason: Optional[str] = Field(default=None)
