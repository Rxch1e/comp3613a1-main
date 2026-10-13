from sqlmodel import Session, select

from app.models.prize import Prize


class PrizeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Prize]:
        return list(self.db.exec(select(Prize).order_by(Prize.hours_cost)).all())

    def get_by_id(self, prize_id: int) -> Prize | None:
        return self.db.get(Prize, prize_id)

    def save(self, prize: Prize) -> Prize:
        self.db.add(prize)
        self.db.commit()
        self.db.refresh(prize)
        return prize
