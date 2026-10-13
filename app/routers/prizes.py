from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.services.prize_service import PrizeService
from app.services.volunteer_hours_service import VolunteerHoursService
from app.utilities.flash import flash
from . import router, templates


@router.get("/app/prizes", response_class=HTMLResponse)
async def prizes_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
    catalog = PrizeService(db).get_catalog(user.id)
    catalog["badge"] = VolunteerHoursService(db).get_badge_info(user.id)
    return templates.TemplateResponse(
        request=request,
        name="prizes.html",
        context={"user": user, **catalog},
    )


@router.post("/app/prizes/{prize_id}/redeem")
async def redeem_prize(
    prize_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
    try:
        redemption = PrizeService(db).redeem(user.id, prize_id)
        message = "Prize redeemed successfully."
        if redemption.status == "pending":
            message = "Prize redeemed and sent for fulfilment."
        flash(request, message)
    except ValueError as error:
        flash(request, str(error), "danger")
    return RedirectResponse(url=request.url_for("prizes_view"), status_code=303)
