from flask import render_template, request, redirect, url_for, flash

from app.auth.routes import login_required
from app.extensions import db
from app.models import ClaimWeek
from app.claims import bp


@bp.route("/")
@login_required
def list_weeks():
    weeks = ClaimWeek.query.order_by(ClaimWeek.start_date).all()
    return render_template("claims/list.html", weeks=weeks)


@bp.route("/<int:week_id>/toggle", methods=["POST"])
@login_required
def toggle_flag(week_id):
    week = ClaimWeek.query.get_or_404(week_id)
    field = request.form.get("field")
    if field not in ("edd_confirmation", "edd_reported_consulting"):
        flash("Unknown field.", "error")
        return redirect(url_for("claims.list_weeks"))
    setattr(week, field, not getattr(week, field))
    db.session.commit()
    return redirect(request.referrer or url_for("claims.list_weeks"))


@bp.route("/<int:week_id>")
@login_required
def week_detail(week_id):
    week = ClaimWeek.query.get_or_404(week_id)
    return render_template("claims/detail.html", week=week)
