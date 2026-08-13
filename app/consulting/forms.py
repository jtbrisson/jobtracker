from flask_wtf import FlaskForm
from wtforms import StringField, DateField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class ConsultingEntryForm(FlaskForm):
    description = StringField("Description", validators=[DataRequired(), Length(max=255)])
    start_date = DateField("Start date", validators=[DataRequired()])
    end_date = DateField("End date", validators=[DataRequired()])
    total_hours = DecimalField("Total hours", validators=[DataRequired(), NumberRange(min=0)], places=2)
    total_earned = DecimalField("Total earned ($)", validators=[DataRequired(), NumberRange(min=0)], places=2)
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")
