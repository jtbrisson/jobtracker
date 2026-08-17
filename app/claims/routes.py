from datetime import date

from flask import render_template, request, redirect, url_for, flash

from app.auth.routes import login_required
from app.extensions import db
from app.models import ClaimWeek
from app.claims import bp
from app.claims.forms import ExpectedAmountForm, BulkAmountForm

# Tri-state cycle for the EDD toggle buttons: No -> Yes -> N/A -> No -> ...
EDD_STATE_CYCLE = [False, True, None]


@bp.route("/")
@login_required
def list_weeks():
    weeks = ClaimWeek.query.order_by(ClaimWeek.start_date).all()
    bulk_form = BulkAmountForm()
    return render_template("claims/list.html", weeks=weeks, bulk_form=bulk_form)


@bp.route("/bulk-amount", methods=["POST"])
@login_required
def bulk_set_amount():
    form = BulkAmountForm()
    if form.validate_on_submit():
        weeks = ClaimWeek.query.filter(ClaimWeek.end_date >= date.today()).all()
        for week in weeks:
            week.expected_edd_amount = form.expected_edd_amount.data
        db.session.commit()
        flash(f"Set expected EDD amount for {len(weeks)} week(s).", "success")
    else:
        flash("Couldn't save that amount.", "error")
    return redirect(url_for("claims.list_weeks"))


@bp.route("/<int:week_id>/toggle", methods=["POST"])
@login_required
def toggle_flag(week_id):
    week = ClaimWeek.query.get_or_404(week_id)
    field = request.form.get("field")
    if field not in ("edd_confirmation", "edd_reported_consulting"):
        flash("Unknown field.", "error")
        return redirect(url_for("claims.list_weeks"))
    current_index = EDD_STATE_CYCLE.index(getattr(week, field))
    setattr(week, field, EDD_STATE_CYCLE[(current_index + 1) % len(EDD_STATE_CYCLE)])
    db.session.commit()
    return redirect(request.referrer or url_for("claims.list_weeks"))


@bp.route("/<int:week_id>")
@login_required
def week_detail(week_id):
    week = ClaimWeek.query.get_or_404(week_id)
    amount_form = ExpectedAmountForm(obj=week)
    return render_template("claims/detail.html", week=week, amount_form=amount_form)


@bp.route("/<int:week_id>/amount", methods=["POST"])
@login_required
def update_amount(week_id):
    week = ClaimWeek.query.get_or_404(week_id)
    form = ExpectedAmountForm()
    if form.validate_on_submit():
        week.expected_edd_amount = form.expected_edd_amount.data
        db.session.commit()
        flash("Expected EDD amount updated.", "success")
    else:
        flash("Couldn't save that amount.", "error")
    return redirect(url_for("claims.week_detail", week_id=week_id))
