from datetime import timedelta

from app.extensions import db
from app.models import ClaimWeek, ClaimSettings


def get_claim_settings():
    """Return the single ClaimSettings row, creating it if it doesn't exist yet."""
    settings = ClaimSettings.query.first()
    if not settings:
        settings = ClaimSettings()
        db.session.add(settings)
        db.session.commit()
    return settings


def is_eligible(week, settings):
    """A week is eligible when it falls inside the claim's start/end date
    range. If the claim dates haven't been set yet, every week counts as
    eligible (keeps existing behavior until the range is configured).
    """
    if not settings.claim_start_date or not settings.claim_end_date:
        return True
    return settings.claim_start_date <= week.start_date <= settings.claim_end_date


def eligible_weeks_query(settings):
    """A ClaimWeek query filtered to the claim's date range, or unfiltered
    if the range hasn't been set yet.
    """
    query = ClaimWeek.query
    if settings.claim_start_date and settings.claim_end_date:
        query = query.filter(
            ClaimWeek.start_date >= settings.claim_start_date,
            ClaimWeek.start_date <= settings.claim_end_date,
        )
    return query


def apply_eligibility_effects(settings, default_amount=450):
    """Run after the claim date range changes: default expected_edd_amount
    to `default_amount` for newly-eligible weeks that don't have an amount
    set yet, and clear EDD confirmation/reported-consulting (back to N/A)
    for weeks that are no longer eligible.
    """
    weeks = ClaimWeek.query.all()
    for week in weeks:
        if is_eligible(week, settings):
            if not week.expected_edd_amount:
                week.expected_edd_amount = default_amount
        else:
            week.edd_confirmation = None
            week.edd_reported_consulting = None
    db.session.commit()


def generate_weeks(start_date, num_weeks, starting_week_number=None):
    """Create `num_weeks` consecutive 7-day ClaimWeek rows starting at
    `start_date`, matching the layout of the uploaded spreadsheet's 'Date'
    table (Week 01, Week 02, ...). Skips any week whose start_date already
    exists. Returns the number of weeks created.

    If `starting_week_number` isn't given, it's derived from `start_date`'s
    real ISO calendar week, so week labels line up with actual ISO weeks.
    """
    if starting_week_number is None:
        starting_week_number = start_date.isocalendar()[1]
    created = 0
    current_start = start_date
    for i in range(num_weeks):
        week_number = starting_week_number + i
        existing = ClaimWeek.query.filter_by(start_date=current_start).first()
        if not existing:
            week = ClaimWeek(
                year=current_start.year,
                week_label=f"Week {week_number:02d}",
                week_number=week_number,
                start_date=current_start,
                end_date=current_start + timedelta(days=6),
            )
            db.session.add(week)
            created += 1
        current_start = current_start + timedelta(days=7)
    db.session.commit()
    return created


def find_week_for_date(a_date):
    """Return the ClaimWeek whose start/end range contains `a_date`, or None."""
    if a_date is None:
        return None
    return ClaimWeek.query.filter(
        ClaimWeek.start_date <= a_date, ClaimWeek.end_date >= a_date
    ).first()


def current_week():
    from datetime import date
    return find_week_for_date(date.today())
