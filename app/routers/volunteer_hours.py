from datetime import date

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.services.volunteer_hours_service import VolunteerHoursService
from app.utilities.flash import flash
from . import router, templates


@router.get("/app/volunteer-hours", response_class=HTMLResponse)
async def volunteer_hours_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
    service = VolunteerHoursService(db)
    summary = service.get_student_submission_summary(user.id)
    
    return templates.TemplateResponse(
        request=request,
        name="volunteer_hours.html",
        context={"user": user, "summary": summary, "today": date.today().isoformat(), "badge": service.get_badge_info(user.id)},
    )


@router.post("/app/volunteer-hours")
async def submit_volunteer_hours(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    event_name: str = Form(),
    hours: float = Form(),
    event_date: date = Form(),
    additional_info: str | None = Form(default=None),
    proof: UploadFile = File(),
):
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
    service = VolunteerHoursService(db)
    try:
        await service.submit_student_log(
            user_id=user.id,
            event_name=event_name,
            hours=hours,
            event_date=event_date,
            additional_info=additional_info,
            proof=proof,
        )
        flash(request, "Volunteer hours submitted for approval.")
    except ValueError as error:
        flash(request, str(error), "danger")
    return RedirectResponse(
        url=request.url_for("volunteer_hours_view"),
        status_code=303,
    )