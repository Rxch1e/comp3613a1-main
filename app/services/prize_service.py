from datetime import datetime

from app.models.prize import Prize
from app.models.redemption import Redemption
from app.repositories.prize import PrizeRepository
from app.repositories.redemption import RedemptionRepository
from app.repositories.volunteer_log import VolunteerLogRepository
from app.repositories.user import UserRepository


class PrizeService:
    DEFAULT_PRIZES = (
        {
            "name": "Campus T-shirt",
            "image_url": "img/prize-shirt.svg",
            "hours_cost": 10,
            "stock": 5,
            "delivery_type": "manual",
        },
        {
            "name": "Recognition Certificate",
            "image_url": "img/prize-certificate.svg",
            "hours_cost": 50,
            "stock": 6,
            "delivery_type": "instant",
        },
        {
            "name": "Apex Medal",
            "image_url": "img/prize-medal.svg",
            "hours_cost": 32,
            "stock": 3,
            "delivery_type": "manual",
        },
    )

    def __init__(self, db):
        self.prize_repo = PrizeRepository(db)
        self.redemption_repo = RedemptionRepository(db)
        self.volunteer_log_repo = VolunteerLogRepository(db)
        self.user_repo = UserRepository(db)

    def get_catalog(self, user_id: int) -> dict:
        approved_hours = sum(
            log.hours
            for log in self.volunteer_log_repo.get_by_user_id(user_id)
            if log.status == "approved"
        )
        redeemed_hours = self.redemption_repo.get_redeemed_hours(user_id)
        redemptions = self.redemption_repo.get_by_user_id(user_id)
        prizes = self._ensure_catalog()
        prizes_by_id = {prize.prize_id: prize for prize in prizes}
        redemption_rows = [
            {
                "redemption": redemption,
                "prize_name": prizes_by_id[redemption.prize_id].name,
                "hours_cost": prizes_by_id[redemption.prize_id].hours_cost,
                "delivery_type": prizes_by_id[redemption.prize_id].delivery_type,
            }
            for redemption in redemptions
            if redemption.prize_id in prizes_by_id
        ]
        return {
            "prizes": list(prizes_by_id.values()),
            "redemptions": redemptions,
            "redemption_rows": redemption_rows,
            "approved_hours": approved_hours,
            "redeemed_hours": redeemed_hours,
            "spendable_balance": max(0, approved_hours - redeemed_hours),
        }

    def _ensure_catalog(self):
        prizes = self.prize_repo.get_all()
        defaults_by_name = {item["name"]: item for item in self.DEFAULT_PRIZES}
        if not prizes:
            for item in self.DEFAULT_PRIZES:
                self.prize_repo.save(Prize(**item))
            return self.prize_repo.get_all()

        for prize in prizes:
            default = defaults_by_name.get(prize.name)
            if default and not prize.image_url:
                prize.image_url = default["image_url"]
                self.prize_repo.save(prize)
        return self.prize_repo.get_all()

    def redeem(self, user_id: int, prize_id: int) -> Redemption:
        self._ensure_catalog()
        prize = self.prize_repo.get_by_id(prize_id)
        if prize is None:
            raise ValueError("Prize not found.")
        if prize.stock <= 0:
            raise ValueError("This prize is out of stock.")

        catalog = self.get_catalog(user_id)
        if catalog["spendable_balance"] < prize.hours_cost:
            raise ValueError("You do not have enough spendable hours.")

        prize.stock -= 1
        self.prize_repo.save(prize)
        now = datetime.utcnow()
        redemption = Redemption(
            user_id=user_id,
            prize_id=prize.prize_id,
            redeemed_at=now,
            fulfilled_at=now if prize.delivery_type == "instant" else None,
            status="fulfilled" if prize.delivery_type == "instant" else "pending",
        )
        return self.redemption_repo.create(redemption)

    def get_pending_fulfilments(self) -> list[dict]:
        prizes = {prize.prize_id: prize for prize in self.prize_repo.get_all()}
        fulfilments = []
        for redemption in self.redemption_repo.get_pending():
            prize = prizes.get(redemption.prize_id)
            user = self.user_repo.get_by_id(redemption.user_id)
            if prize is None:
                continue
            fulfilments.append(
                {
                    "redemption": redemption,
                    "prize_name": prize.name,
                    "hours_cost": prize.hours_cost,
                    "student_name": user.username if user else "Unknown student",
                }
            )
        return fulfilments

    def fulfill(self, redemption_id: int) -> None:
        self.redemption_repo.fulfill(redemption_id)
