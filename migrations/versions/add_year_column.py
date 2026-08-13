"""Add year column to claim_weeks

Revision ID: add_year_column
Revises: github_oauth
Create Date: 2026-08-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_year_column'
down_revision = 'github_oauth'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('claim_weeks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('year', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_claim_weeks_year'), ['year'], unique=False)


def downgrade():
    with op.batch_alter_table('claim_weeks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_claim_weeks_year'))
        batch_op.drop_column('year')
