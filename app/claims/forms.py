from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class ExpectedAmountForm(FlaskForm):
    expected_edd_amount = DecimalField(
        "Expected EDD amount ($)", validators=[DataRequired(), NumberRange(min=0)], places=2
    )
    submit = SubmitField("Save")


class BulkAmountForm(FlaskForm):
    expected_edd_amount = DecimalField(
        "Weekly benefit amount ($)", validators=[DataRequired(), NumberRange(min=0)], places=2
    )
    submit = SubmitField("Apply to this week and all weeks ahead")
