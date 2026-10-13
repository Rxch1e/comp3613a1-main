from typing import Optional

from sqlmodel import Field, SQLModel


class Prize(SQLModel, table=True):
    prize_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    image_url: Optional[str] = None
    hours_cost: float
    stock: int
    delivery_type: str = "manual"
