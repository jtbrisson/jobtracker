from flask import render_template, redirect, url_for, flash, current_app

from app.auth.routes import login_required
from app.extensions import db
from app.models import JobApplication
from app.claims.utils import find_week_for_date
from app.applications import bp
from app.applications.forms import JobApplicationForm
from app import storage


@bp.route("/")
@login_required
def list_applications():
    applications = JobApplication.query.order_by(JobApplication.application_date.desc()).all()
    return render_template("applications/list.html", applications=applications)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new_application():
    form = JobApplicationForm()
    if form.validate_on_submit():
        app_row = JobApplication(
            application_date=form.application_date.data,
            company=form.company.data,
            position=form.position.data,
            status=form.status.data,
            job_description_text=form.job_description_text.data,
            notes=form.notes.data,
        )
        app_row.claim_week_id = getattr(find_week_for_date(app_row.application_date), "id", None)
        db.session.add(app_row)
        db.session.flush()  # get app_row.id for storage keys

        _handle_uploads(app_row, form)

        db.session.commit()
        flash("Application saved.", "success")
        return redirect(url_for("applications.list_applications"))
    return render_template("applications/form.html", form=form, application=None)


@bp.route("/<int:application_id>/edit", methods=["GET", "POST"])
@login_required
def edit_application(application_id):
    app_row = JobApplication.query.get_or_404(application_id)
    form = JobApplicationForm(obj=app_row)
    if form.validate_on_submit():
        app_row.application_date = form.application_date.data
        app_row.company = form.company.data
        app_row.position = form.position.data
        app_row.status = form.status.data
        app_row.job_description_text = form.job_description_text.data
        app_row.notes = form.notes.data
        app_row.claim_week_id = getattr(find_week_for_date(app_row.application_date), "id", None)

        _handle_uploads(app_row, form)

        db.session.commit()
        flash("Application updated.", "success")
        return redirect(url_for("applications.list_applications"))
    return render_template("applications/form.html", form=form, application=app_row)


@bp.route("/<int:application_id>/delete", methods=["POST"])
@login_required
def delete_application(application_id):
    app_row = JobApplication.query.get_or_404(application_id)
    if storage.is_configured():
        for key in (app_row.resume_key, app_row.cover_letter_key, app_row.job_description_key):
            try:
                storage.delete_file(key)
            except Exception as exc:  # pragma: no cover
                current_app.logger.warning("Failed to delete %s: %s", key, exc)
    db.session.delete(app_row)
    db.session.commit()
    flash("Application deleted.", "success")
    return redirect(url_for("applications.list_applications"))


@bp.route("/<int:application_id>/file/<field_name>")
@login_required
def download_file(application_id, field_name):
    app_row = JobApplication.query.get_or_404(application_id)
    key_map = {
        "resume": (app_row.resume_key, app_row.resume_filename),
        "cover_letter": (app_row.cover_letter_key, app_row.cover_letter_filename),
        "job_description": (app_row.job_description_key, app_row.job_description_filename),
    }
    key, filename = key_map.get(field_name, (None, None))
    if not key:
        flash("No file on record.", "error")
        return redirect(url_for("applications.list_applications"))
    url = storage.presigned_download_url(key, filename=filename)
    return redirect(url)


def _handle_uploads(app_row, form):
    """Upload any provided files to object storage and store the resulting
    key/filename/content-type on the JobApplication row. Silently skipped
    (with a flash warning) if storage isn't configured yet, so the rest of
    the form still saves.
    """
    from flask import flash as _flash

    fields = [
        ("resume_file", "resume_key", "resume_filename", "resume_content_type", "resume"),
        ("cover_letter_file", "cover_letter_key", "cover_letter_filename", "cover_letter_content_type", "cover_letter"),
        ("job_description_file", "job_description_key", "job_description_filename", "job_description_content_type", "job_description"),
    ]
    any_file_provided = any(getattr(form, f[0]).data and getattr(form, f[0]).data.filename for f in fields)
    if any_file_provided and not storage.is_configured():
        _flash("File storage isn't configured yet (see .env S3_* settings) — files were not uploaded.", "error")
        return

    for form_field, key_attr, filename_attr, content_type_attr, field_name in fields:
        file_storage = getattr(form, form_field).data
        if file_storage and file_storage.filename:
            key, filename, content_type = storage.upload_file(
                file_storage, application_id=app_row.id, field_name=field_name
            )
            setattr(app_row, key_attr, key)
            setattr(app_row, filename_attr, filename)
            setattr(app_row, content_type_attr, content_type)
