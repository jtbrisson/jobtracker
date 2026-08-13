"""Allow NULL (N/A) on claim_weeks EDD columns

Revision ID: edd_tristate
Revises: add_year_column
Create Date: 2026-08-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edd_tristate'
down_revision = 'add_year_column'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('claim_weeks', schema=None) as batch_op:
        batch_op.alter_column('edd_confirmation', existing_type=sa.Boolean(), nullable=True)
        batch_op.alter_column('edd_reported_consulting', existing_type=sa.Boolean(), nullable=True)


def downgrade():
    with op.batch_alter_table('claim_weeks', schema=None) as batch_op:
        batch_op.alter_column('edd_reported_consulting', existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column('edd_confirmation', existing_type=sa.Boolean(), nullable=False)
