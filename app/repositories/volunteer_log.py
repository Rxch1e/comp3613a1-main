from sqlmodel import Session, select

from app.models.volunteer_log import VolunteerLog


class VolunteerLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> list[VolunteerLog]:
        statement = (
            select(VolunteerLog)
            .where(VolunteerLog.user_id == user_id)
            .order_by(VolunteerLog.submitted_at.desc())
        )
        return list(self.db.exec(statement).all())

    def create(self, volunteer_log: VolunteerLog) -> VolunteerLog:
        self.db.add(volunteer_log)
        self.db.commit()
        self.db.refresh(volunteer_log)
        return volunteer_log

    def get_pending(self) -> list[VolunteerLog]:
        statement = (
            select(VolunteerLog)
            .where(VolunteerLog.status == "pending")
            .order_by(VolunteerLog.submitted_at.asc())
        )
        return list(self.db.exec(statement).all())

    def get_approved(self) -> list[VolunteerLog]:
        statement = select(VolunteerLog).where(VolunteerLog.status == "approved")
        return list(self.db.exec(statement).all())

    def update_status(
        self,
        log_id: int,
        status: str,
        rejection_reason: str | None = None,
    ) -> VolunteerLog:
        volunteer_log = self.db.get(VolunteerLog, log_id)
        if volunteer_log is None:
            raise ValueError("Volunteer log not found.")
        volunteer_log.status = status
        volunteer_log.rejection_reason = rejection_reason
        self.db.add(volunteer_log)
        self.db.commit()
        self.db.refresh(volunteer_log)
        return volunteer_log
