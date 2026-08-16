"""Add expected_edd_amount to claim_weeks

Revision ID: edd_expected_amount
Revises: edd_tristate
Create Date: 2026-08-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edd_expected_amount'
down_revision = 'edd_tristate'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('claim_weeks', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'expected_edd_amount', sa.Numeric(10, 2), nullable=False, server_default='0'
        ))


def downgrade():
    with op.batch_alter_table('claim_weeks', schema=None) as batch_op:
        batch_op.drop_column('expected_edd_amount')
