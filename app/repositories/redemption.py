from datetime import datetime

from sqlmodel import Session, select

from app.models.prize import Prize
from app.models.redemption import Redemption


class RedemptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> list[Redemption]:
        statement = (
            select(Redemption)
            .where(Redemption.user_id == user_id)
            .order_by(Redemption.redeemed_at.desc())
        )
        return list(self.db.exec(statement).all())

    def get_redeemed_hours(self, user_id: int) -> float:
        statement = (
            select(Redemption, Prize)
            .join(Prize, Redemption.prize_id == Prize.prize_id)
            .where(Redemption.user_id == user_id)
        )
        return sum(prize.hours_cost for _, prize in self.db.exec(statement).all())

    def create(self, redemption: Redemption) -> Redemption:
        self.db.add(redemption)
        self.db.commit()
        self.db.refresh(redemption)
        return redemption

    def get_pending(self) -> list[Redemption]:
        statement = (
            select(Redemption)
            .where(Redemption.status == "pending")
            .order_by(Redemption.redeemed_at.asc())
        )
        return list(self.db.exec(statement).all())

    def fulfill(self, redemption_id: int) -> Redemption:
        redemption = self.db.get(Redemption, redemption_id)
        if redemption is None:
            raise ValueError("Redemption not found.")
        redemption.status = "fulfilled"
        redemption.fulfilled_at = datetime.utcnow()
        self.db.add(redemption)
        self.db.commit()
        self.db.refresh(redemption)
        return redemption
