from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from app.services.volunteer_hours_service import VolunteerHoursService
from app.services.prize_service import PrizeService
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
    service = VolunteerHoursService(db)
    logs = service.get_student_logs(user.id)
    approved_hours = sum(log.hours for log in logs if log.status == "approved")
    pending_hours = sum(log.hours for log in logs if log.status == "pending")
    badge = service.get_badge_info(user.id)
    leaderboard = service.get_leaderboard(user.id)
    progress = service.get_progress(user.id)
    upcoming_events = service.get_upcoming_events()
    prize_summary = PrizeService(db).get_catalog(user.id)
    next_milestone = next((item for item in progress["milestones"] if not item["achieved"]), progress["milestones"][-1])
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "logs": logs,
            "approved_hours": approved_hours,
            "pending_hours": pending_hours,
            "badge": badge,
            "leaderboard": leaderboard,
            "progress": progress,
            "next_milestone": next_milestone,
            "spendable_balance": prize_summary["spendable_balance"],
            "upcoming_events": upcoming_events,
        }
    )