from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.models.volunteer_log import VolunteerLog
from app.repositories.volunteer_log import VolunteerLogRepository
from app.repositories.user import UserRepository
from app.repositories.prize import PrizeRepository
from app.repositories.redemption import RedemptionRepository


class VolunteerHoursService:
    UPCOMING_EVENTS = (
        {"name": "Campus Clean-up Day", "date": "Oct 18, 2026", "location": "North Quad", "hours": 4},
        {"name": "Food Bank Collection", "date": "Oct 24, 2026", "location": "Student Centre", "hours": 3},
        {"name": "Alumni Mentorship Fair", "date": "Nov 02, 2026", "location": "Main Hall", "hours": 5},
    )

    MILESTONES = (
        {
            "title": "Bronze",
            "badge": "Bronze",
            "badge_icon": "military_tech",
            "required_hours": 25,
            "unlock_text": "Unlocks Bronze Profile Badge & Basic Rewards Tier",
        },
        {
            "title": "Silver",
            "badge": "Silver",
            "badge_icon": "workspace_premium",
            "required_hours": 50,
            "unlock_text": "Unlocks Silver Profile Badge & Mid-tier Rewards",
        },
        {
            "title": "Gold",
            "badge": "Gold",
            "badge_icon": "emoji_events",
            "required_hours": 150,
            "unlock_text": "Unlocks Gold Profile Badge & Elite Rewards Tier",
        },
    )

    def __init__(self, db):
        self.volunteer_log_repo = VolunteerLogRepository(db)
        self.user_repo = UserRepository(db)
        self.prize_repo = PrizeRepository(db)
        self.redemption_repo = RedemptionRepository(db)

    def get_student_logs(self, user_id: int):
        return self.volunteer_log_repo.get_by_user_id(user_id)

    def get_student_submission_summary(self, user_id: int) -> dict:
        logs = self.volunteer_log_repo.get_by_user_id(user_id)
        pending = [log for log in logs if log.status == "pending"]
        rejected = [log for log in logs if log.status == "rejected"]
        return {
            "pending": pending,
            "pending_hours": sum(log.hours for log in pending),
            "rejected": rejected,
        }

    async def submit_student_log(
        self,
        user_id: int,
        event_name: str,
        hours: float,
        event_date: date,
        additional_info: str | None,
        proof: UploadFile,
    ) -> VolunteerLog:
        if hours <= 0:
            raise ValueError("Hours must be greater than 0.")
        if event_date > date.today():
            raise ValueError("Event date cannot be in the future.")
        if not proof.content_type or not proof.content_type.startswith("image/"):
            raise ValueError("Proof must be an image file.")

        upload_dir = Path("app/static/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(proof.filename or "proof").suffix.lower()
        filename = f"{uuid4().hex}{suffix}"
        upload_path = upload_dir / filename
        upload_path.write_bytes(await proof.read())

        volunteer_log = VolunteerLog(
            user_id=user_id,
            event_name=event_name.strip(),
            hours=hours,
            event_date=event_date,
            submitted_at=datetime.utcnow(),
            proof=f"uploads/{filename}",
            additional_info=additional_info.strip() if additional_info else None,
        )
        return self.volunteer_log_repo.create(volunteer_log)

    def get_pending_submissions(self) -> list[dict]:
        submissions = []
        for volunteer_log in self.volunteer_log_repo.get_pending():
            student = self.user_repo.get_by_id(volunteer_log.user_id)
            submissions.append(
                {
                    "log": volunteer_log,
                    "student_name": student.username if student else "Unknown student",
                }
            )
        return submissions

    def approve_submission(self, log_id: int) -> None:
        self.volunteer_log_repo.update_status(log_id, "approved")

    def reject_submission(self, log_id: int, rejection_reason: str) -> None:
        reason = rejection_reason.strip()
        if not reason:
            raise ValueError("A rejection reason is required.")
        self.volunteer_log_repo.update_status(log_id, "rejected", reason)

    def get_progress(self, user_id: int) -> dict:
        approved_logs = [
            log
            for log in self.volunteer_log_repo.get_by_user_id(user_id)
            if log.status == "approved"
        ]
        approved_logs.sort(key=lambda log: (log.event_date, log.submitted_at))
        approved_hours = sum(log.hours for log in approved_logs)
        milestones = []
        for milestone in self.MILESTONES:
            required_hours = milestone["required_hours"]
            running_hours = 0
            reached_date = None
            for log in approved_logs:
                running_hours += log.hours
                if running_hours >= required_hours:
                    reached_date = log.event_date
                    break
            if reached_date:
                state = "Unlocked"
                status_text = f"{required_hours}-hour milestone reached"
            elif approved_hours:
                state = "In progress"
                status_text = f"{approved_hours:g} / {required_hours} lifetime hours"
            else:
                state = "Locked"
                status_text = f"0 / {required_hours} lifetime hours"
            milestones.append(
                {
                    **milestone,
                    "achieved": approved_hours >= required_hours,
                    "percent": min(100, round(approved_hours / required_hours * 100)),
                    "state": state,
                    "status_text": status_text,
                    "reached_date": reached_date,
                    "remaining_hours": max(0, required_hours - approved_hours),
                }
            )
        return {"approved_hours": approved_hours, "milestones": milestones}

    def get_badge_info(self, user_id: int) -> dict:
        progress = self.get_progress(user_id)
        unlocked = [milestone for milestone in progress["milestones"] if milestone["achieved"]]
        if not unlocked:
            return {
                "name": "No badge yet",
                "icon": "star_border",
                "color": "neutral",
                "reached_date": None,
            }
        latest = unlocked[-1]
        return {
            "name": latest["badge"],
            "icon": latest["badge_icon"],
            "color": latest["badge"].lower(),
            "reached_date": latest["reached_date"],
        }

    def get_admin_stats(self) -> dict:
        pending_submissions = self.volunteer_log_repo.get_pending()
        pending_fulfilments = self.redemption_repo.get_pending()
        students = [user for user in self.user_repo.get_all_users() if user.role != "admin"]
        return {
            "pending_submissions": len(pending_submissions),
            "out_of_stock_prizes": sum(1 for prize in self.prize_repo.get_all() if prize.stock <= 0),
            "pending_redemptions": len(pending_fulfilments),
            "student_volunteers": len(students),
        }

    def get_leaderboard(self, user_id: int, badge_filter: str = "", letter_filter: str = "", show_all: bool = False) -> dict:
        totals: dict[int, float] = {}
        for log in self.volunteer_log_repo.get_approved():
            totals[log.user_id] = totals.get(log.user_id, 0) + log.hours

        leaderboard = []
        for student in self.user_repo.get_all_users():
            if student.role == "admin":
                continue
            lifetime_hours = totals.get(student.id, 0)
            leaderboard.append(
                {
                    "user_id": student.id,
                    "username": student.username,
                    "hours": lifetime_hours,
                    "highest_badge": self._highest_badge(lifetime_hours),
                    "badge_icon": self._highest_badge_icon(lifetime_hours),
                    "is_current_user": student.id == user_id,
                }
            )
        leaderboard.sort(key=lambda entry: (-entry["hours"], entry["username"].lower()))
        for rank, entry in enumerate(leaderboard, start=1):
            entry["rank"] = rank
        current = next((entry for entry in leaderboard if entry["is_current_user"]), None)
        filtered = leaderboard
        if badge_filter:
            filtered = [entry for entry in filtered if entry["highest_badge"].lower() == badge_filter.lower()]
        if letter_filter:
            filtered = [entry for entry in filtered if entry["username"].lower().startswith(letter_filter.lower())]
        return {
            "entries": filtered if badge_filter or letter_filter or show_all else leaderboard[:10],
            "current_rank": current["rank"] if current else None,
            "lifetime_hours": current["hours"] if current else 0,
            "total_participants": len(leaderboard),
            "badge_filter": badge_filter,
            "letter_filter": letter_filter,
            "show_all": show_all,
        }

    def get_upcoming_events(self) -> list[dict]:
        return list(self.UPCOMING_EVENTS)

    def _highest_badge(self, hours: float) -> str:
        highest = "Not yet unlocked"
        for milestone in self.MILESTONES:
            if hours >= milestone["required_hours"]:
                highest = milestone["badge"]
        return highest

    def _highest_badge_icon(self, hours: float) -> str:
        icon = "star_border"
        for milestone in self.MILESTONES:
            if hours >= milestone["required_hours"]:
                icon = milestone["badge_icon"]
        return icon
