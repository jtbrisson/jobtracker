from datetime import date, timedelta

from flask import render_template

from app.auth.routes import login_required
from app.models import ClaimWeek, JobApplication, ConsultingEntry
from app.claims.utils import current_week, get_claim_settings, eligible_weeks_query
from app.dashboard import bp


@bp.route("/")
@login_required
def home():
    this_week = current_week()

    upcoming_weeks = (
        ClaimWeek.query.filter(ClaimWeek.start_date >= date.today() - timedelta(days=7))
        .order_by(ClaimWeek.start_date)
        .limit(4)
        .all()
    )

    recent_applications = (
        JobApplication.query.order_by(JobApplication.application_date.desc()).limit(5).all()
    )
    recent_consulting = (
        ConsultingEntry.query.order_by(ConsultingEntry.start_date.desc()).limit(5).all()
    )

    claim_settings = get_claim_settings()

    total_applications = JobApplication.query.count()
    unconfirmed_weeks = eligible_weeks_query(claim_settings).filter(
        ClaimWeek.end_date < date.today(), ClaimWeek.edd_confirmation.isnot(True)
    ).count()
    total_net_edd = sum(w.net_edd_amount for w in eligible_weeks_query(claim_settings).all())
    remaining_net_edd = sum(
        w.net_edd_amount
        for w in eligible_weeks_query(claim_settings).filter(ClaimWeek.end_date >= date.today()).all()
    )

    return render_template(
        "dashboard.html",
        this_week=this_week,
        upcoming_weeks=upcoming_weeks,
        recent_applications=recent_applications,
        recent_consulting=recent_consulting,
        total_applications=total_applications,
        unconfirmed_weeks=unconfirmed_weeks,
        total_net_edd=total_net_edd,
        remaining_net_edd=remaining_net_edd,
    )
