from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class ExpectedAmountForm(FlaskForm):
    expected_edd_amount = DecimalField(
        "Expected EDD amount ($)", validators=[DataRequired(), NumberRange(min=0)], places=2
    )
    submit = SubmitField("Save")
