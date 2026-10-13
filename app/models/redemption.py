from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Redemption(SQLModel, table=True):
    redemption_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    prize_id: int = Field(foreign_key="prize.prize_id", index=True)
    redeemed_at: datetime = Field(default_factory=datetime.utcnow)
    fulfilled_at: Optional[datetime] = None
    status: str = "pending"
