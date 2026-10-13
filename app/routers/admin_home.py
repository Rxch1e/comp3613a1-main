from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.services.volunteer_hours_service import VolunteerHoursService
from app.services.prize_service import PrizeService
from app.utilities.flash import flash
from . import router, templates


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    service = VolunteerHoursService(db)
    submissions = service.get_pending_submissions()
    prize_fulfilments = PrizeService(db).get_pending_fulfilments()
    stats = service.get_admin_stats()
    return templates.TemplateResponse(
        request=request, 
        name="admin.html",
        context={
            "user": user,
            "submissions": submissions,
            "prize_fulfilments": prize_fulfilments,
            "stats": stats,
        }
    )


@router.post("/admin/volunteer-hours/{log_id}/approve")
async def approve_volunteer_hours(
    log_id: int,
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    VolunteerHoursService(db).approve_submission(log_id)
    flash(request, "Volunteer hours approved.")
    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)


@router.post("/admin/redemptions/{redemption_id}/fulfill")
async def fulfill_prize_redemption(
    redemption_id: int,
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    PrizeService(db).fulfill(redemption_id)
    flash(request, "Prize redemption fulfilled.")
    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)


@router.post("/admin/volunteer-hours/{log_id}/reject")
async def reject_volunteer_hours(
    log_id: int,
    request: Request,
    user: AdminDep,
    db: SessionDep,
    rejection_reason: str = Form(),
):
    try:
        VolunteerHoursService(db).reject_submission(log_id, rejection_reason)
        flash(request, "Volunteer hours rejected.")
    except ValueError as error:
        flash(request, str(error), "danger")
    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
