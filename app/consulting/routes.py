from flask import render_template, redirect, url_for, flash

from app.auth.routes import login_required
from app.extensions import db
from app.models import ConsultingEntry
from app.claims.utils import find_week_for_date
from app.consulting import bp
from app.consulting.forms import ConsultingEntryForm


@bp.route("/")
@login_required
def list_entries():
    entries = ConsultingEntry.query.order_by(ConsultingEntry.start_date.desc()).all()
    return render_template("consulting/list.html", entries=entries)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new_entry():
    form = ConsultingEntryForm()
    if form.validate_on_submit():
        entry = ConsultingEntry(
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            total_hours=form.total_hours.data,
            total_earned=form.total_earned.data,
            notes=form.notes.data,
        )
        entry.claim_week_id = getattr(find_week_for_date(entry.start_date), "id", None)
        db.session.add(entry)
        db.session.commit()
        flash("Consulting entry saved.", "success")
        return redirect(url_for("consulting.list_entries"))
    return render_template("consulting/form.html", form=form, entry=None)


@bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = ConsultingEntry.query.get_or_404(entry_id)
    form = ConsultingEntryForm(obj=entry)
    if form.validate_on_submit():
        entry.description = form.description.data
        entry.start_date = form.start_date.data
        entry.end_date = form.end_date.data
        entry.total_hours = form.total_hours.data
        entry.total_earned = form.total_earned.data
        entry.notes = form.notes.data
        entry.claim_week_id = getattr(find_week_for_date(entry.start_date), "id", None)
        db.session.commit()
        flash("Consulting entry updated.", "success")
        return redirect(url_for("consulting.list_entries"))
    return render_template("consulting/form.html", form=form, entry=entry)


@bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    entry = ConsultingEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("Consulting entry deleted.", "success")
    return redirect(url_for("consulting.list_entries"))
