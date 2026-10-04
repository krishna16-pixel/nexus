"""Add contact details for rental handover notifications.

Revision ID: e7f8contact01
Revises: d5e6rent01
Create Date: 2026-10-04
"""
from alembic import op
import sqlalchemy as sa

revision = "e7f8contact01"
down_revision = "d5e6rent01"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("address", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("address")
        batch_op.drop_column("phone")
