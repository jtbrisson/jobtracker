from datetime import timedelta

from app.extensions import db
from app.models import ClaimWeek


def generate_weeks(start_date, num_weeks, starting_week_number=1):
    """Create `num_weeks` consecutive 7-day ClaimWeek rows starting at
    `start_date`, matching the layout of the uploaded spreadsheet's 'Date'
    table (Week 01, Week 02, ...). Skips any week whose start_date already
    exists. Returns the number of weeks created.
    """
    created = 0
    current_start = start_date
    for i in range(num_weeks):
        week_number = starting_week_number + i
        existing = ClaimWeek.query.filter_by(start_date=current_start).first()
        if not existing:
            week = ClaimWeek(
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
