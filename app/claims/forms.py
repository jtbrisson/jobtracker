from flask_wtf import FlaskForm
from wtforms import DecimalField, DateField, SubmitField
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


class ClaimSettingsForm(FlaskForm):
    claim_start_date = DateField("Claim start date", validators=[DataRequired()])
    claim_end_date = DateField("Claim end date", validators=[DataRequired()])
    max_benefit_amount = DecimalField(
        "Max benefit possible ($)", validators=[DataRequired(), NumberRange(min=0)], places=2
    )
    submit = SubmitField("Save claim details")
