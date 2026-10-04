"""Add notifications + rentals for BookCircle rent flow

Revision ID: d5e6rent01
Revises: c4c1circle01
Create Date: 2026-10-01

Additive only — no changes to existing tables.
"""
from alembic import op
import sqlalchemy as sa


revision = 'd5e6rent01'
down_revision = 'c4c1circle01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('link', sa.String(length=255), nullable=True),
        sa.Column('ref_type', sa.String(length=50), nullable=True),
        sa.Column('ref_id', sa.String(length=64), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notifications_user_id'), ['user_id'], unique=False)

    op.create_table('rentals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('listing_id', sa.UUID(), nullable=False),
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('renter_id', sa.UUID(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('return_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_due_reminder_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fine_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('amount_collected', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_note', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('active', 'return_requested', 'returned', name='rentalstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['circle_claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['circle_listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['renter_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_id')
    )
    with op.batch_alter_table('rentals', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rentals_listing_id'), ['listing_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_rentals_renter_id'), ['renter_id'], unique=False)


def downgrade():
    with op.batch_alter_table('rentals', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rentals_renter_id'))
        batch_op.drop_index(batch_op.f('ix_rentals_listing_id'))
    op.drop_table('rentals')
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notifications_user_id'))
    op.drop_table('notifications')
