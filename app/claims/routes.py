from datetime import date

from flask import render_template, request, redirect, url_for, flash

from app.auth.routes import login_required
from app.extensions import db
from app.models import ClaimWeek
from app.claims import bp
from app.claims.forms import ExpectedAmountForm, BulkAmountForm, ClaimSettingsForm
from app.claims.utils import (
    get_claim_settings, is_eligible, eligible_weeks_query, apply_eligibility_effects, current_week,
)

# Tri-state cycle for the EDD toggle buttons: No -> Yes -> N/A -> No -> ...
EDD_STATE_CYCLE = [False, True, None]


@bp.route("/")
@login_required
def list_weeks():
    weeks = ClaimWeek.query.order_by(ClaimWeek.start_date).all()
    settings = get_claim_settings()
    for week in weeks:
        week.is_eligible = is_eligible(week, settings)
    bulk_form = BulkAmountForm()
    claim_form = ClaimSettingsForm(obj=settings)
    this_week = current_week()
    return render_template(
        "claims/list.html", weeks=weeks, bulk_form=bulk_form, claim_form=claim_form,
        this_week_id=this_week.id if this_week else None,
    )


@bp.route("/claim-settings", methods=["POST"])
@login_required
def update_claim_settings():
    settings = get_claim_settings()
    form = ClaimSettingsForm()
    if form.validate_on_submit():
        settings.claim_start_date = form.claim_start_date.data
        settings.claim_end_date = form.claim_end_date.data
        settings.max_benefit_amount = form.max_benefit_amount.data
        db.session.commit()
        apply_eligibility_effects(settings)
        flash("Claim details saved.", "success")
    else:
        flash("Couldn't save claim details.", "error")
    return redirect(url_for("claims.list_weeks"))


@bp.route("/bulk-amount", methods=["POST"])
@login_required
def bulk_set_amount():
    form = BulkAmountForm()
    if form.validate_on_submit():
        settings = get_claim_settings()
        weeks = eligible_weeks_query(settings).filter(ClaimWeek.end_date >= date.today()).all()
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
    settings = get_claim_settings()
    if not is_eligible(week, settings):
        flash("This week is outside your claim period.", "error")
        return redirect(request.referrer or url_for("claims.list_weeks"))
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
    settings = get_claim_settings()
    week.is_eligible = is_eligible(week, settings)
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
