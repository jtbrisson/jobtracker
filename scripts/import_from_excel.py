"""One-time importer that reads the original 'Job Tracker App.xlsx' template
(the 'Date' table: ISO Week No / Start Date / End Date) and creates matching
ClaimWeek rows, so the live app starts with the exact same weeks you already
laid out in Excel instead of only relying on BENEFIT_YEAR_START/WEEKS in
config.

Usage (from the project root, with your venv active and .env loaded):
    flask shell   # sanity check app context works, or:
    python scripts/import_from_excel.py path/to/Job_Tracker_App.xlsx
"""
import re
import sys
from datetime import datetime

import openpyxl

sys.path.insert(0, ".")

from app import create_app
from app.extensions import db
from app.models import ClaimWeek

MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December"
)
DATE_RE = re.compile(rf"({MONTHS})\s+(\d{{1,2}}),\s*(\d{{4}})")


def parse_excel_date(cell_value):
    """The template stores dates as text like 'December\\xa029,\\xa02026'."""
    if cell_value is None:
        return None
    text = str(cell_value).replace("\xa0", " ")
    m = DATE_RE.search(text)
    if not m:
        return None
    month, day, year = m.groups()
    return datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()


def import_weeks(xlsx_path, sheet_name=None):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.worksheets[0]

    created = 0
    for row in ws.iter_rows(values_only=True):
        if not row or row[2] is None:
            continue
        label = str(row[2]).strip()
        if not label.lower().startswith("week"):
            continue
        start_date = parse_excel_date(row[3]) if len(row) > 3 else None
        end_date = parse_excel_date(row[4]) if len(row) > 4 else None
        if not start_date or not end_date:
            continue

        week_number_match = re.search(r"(\d+)", label)
        week_number = int(week_number_match.group(1)) if week_number_match else created + 1

        existing = ClaimWeek.query.filter_by(start_date=start_date).first()
        if existing:
            continue

        db.session.add(ClaimWeek(
            week_label=label,
            week_number=week_number,
            start_date=start_date,
            end_date=end_date,
        ))
        created += 1

    db.session.commit()
    return created


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_from_excel.py path/to/Job_Tracker_App.xlsx")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        count = import_weeks(sys.argv[1])
        print(f"Created {count} claim week(s) from {sys.argv[1]}.")
