"""Manual smoke test (not pytest) exercising the main flows against the
local SQLite dev DB: login gate, dashboard, claim weeks, and full CRUD for
job applications and consulting entries. Run with the venv active:
    python tests/smoke_test.py
"""
import io
import sys

sys.path.insert(0, ".")

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()


def login_session(client):
    with app.app_context():
        user = User.query.filter_by(email="jtbrisson@gmail.com").first()
        if not user:
            user = User(email="jtbrisson@gmail.com", name="Joelle")
            db.session.add(user)
            db.session.commit()
        user_id = user.id
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_email"] = "jtbrisson@gmail.com"
        sess["user_name"] = "Joelle"


def check(label, resp, expect=200):
    status = resp.status_code
    ok = status == expect
    print(f"[{'OK' if ok else 'FAIL'}] {label}: {status}")
    if not ok:
        print(resp.get_data(as_text=True)[:800])
    assert ok, f"{label} expected {expect} got {status}"


def main():
    client = app.test_client()

    # Unauthenticated dashboard should redirect to login
    resp = client.get("/")
    check("GET / (unauthenticated) redirects", resp, expect=302)

    resp = client.get("/auth/login")
    check("GET /auth/login", resp)

    login_session(client)

    resp = client.get("/")
    check("GET / (dashboard)", resp)

    resp = client.get("/weeks/")
    check("GET /weeks/", resp)

    resp = client.get("/applications/")
    check("GET /applications/", resp)

    resp = client.get("/consulting/")
    check("GET /consulting/", resp)

    # Create a job application (no file uploads, since storage isn't configured)
    resp = client.get("/applications/new")
    check("GET /applications/new", resp)

    # Extract CSRF token
    html = resp.get_data(as_text=True)
    import re
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    csrf = m.group(1) if m else None
    assert csrf, "CSRF token not found in form"

    resp = client.post("/applications/new", data={
        "csrf_token": csrf,
        "application_date": "2026-01-05",
        "company": "Acme Corp",
        "position": "Staff Engineer",
        "status": "Applied",
        "job_description_text": "Build cool things.",
        "notes": "Referred by a friend.",
    }, content_type="multipart/form-data", follow_redirects=True)
    check("POST /applications/new", resp)
    assert "Acme Corp" in resp.get_data(as_text=True)

    with app.app_context():
        from app.models import JobApplication, ClaimWeek
        app_row = JobApplication.query.filter_by(company="Acme Corp").first()
        assert app_row is not None, "Application was not created"
        assert app_row.claim_week_id is not None, "Application not linked to a claim week"
        week = ClaimWeek.query.get(app_row.claim_week_id)
        print(f"[OK] Application linked to {week.week_label} ({week.start_date}..{week.end_date})")
        assert week.jobs_applied_count == 1

    # Create a consulting entry
    resp = client.get("/consulting/new")
    html = resp.get_data(as_text=True)
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    csrf = m.group(1)

    resp = client.post("/consulting/new", data={
        "csrf_token": csrf,
        "description": "Website consulting for Bob's Shop",
        "start_date": "2026-01-06",
        "end_date": "2026-01-06",
        "total_hours": "4",
        "total_earned": "400",
        "notes": "",
    }, follow_redirects=True)
    check("POST /consulting/new", resp)
    assert "Bob" in resp.get_data(as_text=True) and "Shop" in resp.get_data(as_text=True)

    with app.app_context():
        from app.models import ClaimWeek
        week = ClaimWeek.query.filter_by(week_label="Week 02").first()
        print(f"[OK] Week 02 totals -> hours: {week.total_consulting_hours}, earned: {week.total_consulting_earned}")
        assert float(week.total_consulting_hours) == 4.0

    # Toggle EDD confirmation flag
    with app.app_context():
        from app.models import ClaimWeek
        week1 = ClaimWeek.query.filter_by(week_label="Week 01").first()
        week1_id = week1.id
    resp = client.post(f"/weeks/{week1_id}/toggle", data={"field": "edd_confirmation"}, follow_redirects=True)
    check("POST /weeks/<id>/toggle", resp)
    with app.app_context():
        from app.models import ClaimWeek
        week1 = ClaimWeek.query.get(week1_id)
        assert week1.edd_confirmation is True
        print("[OK] EDD confirmation toggled to True")

    with app.app_context():
        from app.models import JobApplication
        app_row = JobApplication.query.filter_by(company="Acme Corp").first()
        app_week_id = app_row.claim_week_id

    resp = client.get(f"/weeks/{app_week_id}")
    check("GET /weeks/<id> detail (application's actual week)", resp)
    assert "Acme Corp" in resp.get_data(as_text=True)

    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
