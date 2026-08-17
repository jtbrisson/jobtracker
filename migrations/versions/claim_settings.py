"""Add claim_settings table

Revision ID: claim_settings
Revises: edd_expected_amount
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'claim_settings'
down_revision = 'edd_expected_amount'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'claim_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_start_date', sa.Date(), nullable=True),
        sa.Column('claim_end_date', sa.Date(), nullable=True),
        sa.Column('max_benefit_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('claim_settings')
