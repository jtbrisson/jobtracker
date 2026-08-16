from datetime import datetime

from app.extensions import db


class User(db.Model):
    """User record backed by GitHub OAuth session.

    This app is single-user by design (access is gated by ALLOWED_GITHUB_USERNAMES in
    config), but we still keep a row so Flask-Login-style session handling
    and audit fields (created_at) have something to point at.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255))
    github_username = db.Column(db.String(255), unique=True)
    avatar_url = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<User {self.email}>"


class ClaimWeek(db.Model):
    """One row per CA EDD certification week (matches the 'Date' table in
    the uploaded spreadsheet: ISO week number, start/end date, and the two
    EDD checkboxes). Job applications and consulting entries are linked to
    the week they fall in so weekly totals can be computed.
    """

    __tablename__ = "claim_weeks"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    week_label = db.Column(db.String(20), nullable=False)  # e.g. "Week 01"
    week_number = db.Column(db.Integer, nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    end_date = db.Column(db.Date, nullable=False)

    # Tri-state: True = Yes, False = No, None = N/A
    edd_confirmation = db.Column(db.Boolean, default=False, nullable=True)
    edd_reported_consulting = db.Column(db.Boolean, default=False, nullable=True)
    expected_edd_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    notes = db.Column(db.Text)

    job_applications = db.relationship(
        "JobApplication", backref="claim_week", lazy="dynamic",
        order_by="JobApplication.application_date",
    )
    consulting_entries = db.relationship(
        "ConsultingEntry", backref="claim_week", lazy="dynamic",
        order_by="ConsultingEntry.start_date",
    )

    @property
    def jobs_applied_count(self):
        return self.job_applications.count()

    @property
    def total_consulting_hours(self):
        total = 0
        for entry in self.consulting_entries:
            total += float(entry.total_hours or 0)
        return total

    @property
    def total_consulting_earned(self):
        total = 0
        for entry in self.consulting_entries:
            total += float(entry.total_earned or 0)
        return total

    @property
    def edd_deduction(self):
        """CA EDD partial-benefit deduction: earnings above $25 or 25% of
        earnings (whichever is greater) reduce the weekly benefit dollar
        for dollar.
        """
        earned = self.total_consulting_earned
        disregard = max(25.0, 0.25 * earned)
        return max(earned - disregard, 0)

    @property
    def net_edd_amount(self):
        expected = float(self.expected_edd_amount or 0)
        return max(expected - self.edd_deduction, 0)

    def __repr__(self):
        return f"<ClaimWeek {self.week_label} {self.start_date}..{self.end_date}>"


class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)
    application_date = db.Column(db.Date, nullable=False, index=True)
    company = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default="Applied", nullable=False)
    job_description_text = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Resume attachment
    resume_key = db.Column(db.String(512))
    resume_filename = db.Column(db.String(255))
    resume_content_type = db.Column(db.String(120))

    # Cover letter attachment
    cover_letter_key = db.Column(db.String(512))
    cover_letter_filename = db.Column(db.String(255))
    cover_letter_content_type = db.Column(db.String(120))

    # Job description attachment (optional, in addition to/instead of the text field)
    job_description_key = db.Column(db.String(512))
    job_description_filename = db.Column(db.String(255))
    job_description_content_type = db.Column(db.String(120))

    claim_week_id = db.Column(db.Integer, db.ForeignKey("claim_weeks.id"), index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    STATUSES = ["Applied", "Phone Screen", "Interviewing", "Offer", "Rejected", "Withdrawn"]

    def __repr__(self):
        return f"<JobApplication {self.company} - {self.position}>"


class ConsultingEntry(db.Model):
    __tablename__ = "consulting_entries"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False)
    total_hours = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    total_earned = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    notes = db.Column(db.Text)

    claim_week_id = db.Column(db.Integer, db.ForeignKey("claim_weeks.id"), index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ConsultingEntry {self.description} {self.start_date}>"
