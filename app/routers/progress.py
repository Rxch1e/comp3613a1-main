from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.services.volunteer_hours_service import VolunteerHoursService
from . import router, templates


@router.get("/app/progress", response_class=HTMLResponse)
async def progress_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)

    service = VolunteerHoursService(db)
    badge_filter = request.query_params.get("badge", "")
    letter_filter = request.query_params.get("letter", "")
    show_all = request.query_params.get("show_all", "") == "1"
    return templates.TemplateResponse(
        request=request,
        name="progress.html",
        context={
            "user": user,
            "progress": service.get_progress(user.id),
            "leaderboard": service.get_leaderboard(user.id, badge_filter, letter_filter, show_all),
            "badge": service.get_badge_info(user.id),
        },
    )
