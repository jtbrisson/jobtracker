from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

ALLOWED_DOC_EXTENSIONS = ["pdf", "doc", "docx", "txt", "rtf", "odt"]


class JobApplicationForm(FlaskForm):
    application_date = DateField("Application date", validators=[DataRequired()])
    company = StringField("Company", validators=[DataRequired(), Length(max=255)])
    position = StringField("Position", validators=[DataRequired(), Length(max=255)])
    status = SelectField(
        "Status",
        choices=[(s, s) for s in
                 ["Applied", "Phone Screen", "Interviewing", "Offer", "Rejected", "Withdrawn"]],
        validators=[DataRequired()],
    )
    job_description_text = TextAreaField("Job description (paste text, optional)", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])

    resume_file = FileField(
        "Resume file",
        validators=[FileAllowed(ALLOWED_DOC_EXTENSIONS, "Unsupported file type.")],
    )
    cover_letter_file = FileField(
        "Cover letter file",
        validators=[FileAllowed(ALLOWED_DOC_EXTENSIONS, "Unsupported file type.")],
    )
    job_description_file = FileField(
        "Job description file (optional, in addition to pasted text)",
        validators=[FileAllowed(ALLOWED_DOC_EXTENSIONS + ["png", "jpg", "jpeg"], "Unsupported file type.")],
    )

    submit = SubmitField("Save")
