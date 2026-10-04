"""Add BookVerse journey: copies, pass, sos, badges

Revision ID: b7c2journey01
Revises: a7aec01dd5ba
Create Date: 2026-09-29

Additive only — no changes to existing tables.
"""
from alembic import op
import sqlalchemy as sa


revision = 'b7c2journey01'
down_revision = 'a7aec01dd5ba'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('book_copies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=False),
        sa.Column('origin_seller_id', sa.UUID(), nullable=False),
        sa.Column('current_owner_id', sa.UUID(), nullable=False),
        sa.Column('source_order_id', sa.UUID(), nullable=True),
        sa.Column('copy_index', sa.Integer(), nullable=False),
        sa.Column('copy_code', sa.String(length=16), nullable=False),
        sa.Column('status', sa.Enum('active', 'inactive', name='copystatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['current_owner_id'], ['users.id']),
        sa.ForeignKeyConstraint(['origin_seller_id'], ['users.id']),
        sa.ForeignKeyConstraint(['source_order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_order_id', 'book_id', 'copy_index', name='uq_copy_order_book_idx')
    )
    with op.batch_alter_table('book_copies', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_book_copies_book_id'), ['book_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_book_copies_copy_code'), ['copy_code'], unique=True)
        batch_op.create_index(batch_op.f('ix_book_copies_current_owner_id'), ['current_owner_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_book_copies_source_order_id'), ['source_order_id'], unique=False)

    op.create_table('copy_transfers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('copy_id', sa.UUID(), nullable=False),
        sa.Column('from_user_id', sa.UUID(), nullable=True),
        sa.Column('to_user_id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=True),
        sa.Column('transfer_type', sa.Enum('purchase', 'resale', 'exchange', 'lend', 'gift', 'sos', name='transfertype'), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['copy_id'], ['book_copies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('copy_transfers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_copy_transfers_copy_id'), ['copy_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_copy_transfers_to_user_id'), ['to_user_id'], unique=False)

    op.create_table('condition_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('copy_id', sa.UUID(), nullable=False),
        sa.Column('reporter_id', sa.UUID(), nullable=False),
        sa.Column('condition_label', sa.Enum('new', 'like_new', 'good', 'fair', 'poor', name='conditionlabel'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['copy_id'], ['book_copies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('condition_reports', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_condition_reports_copy_id'), ['copy_id'], unique=False)

    op.create_table('copy_discussions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('copy_id', sa.UUID(), nullable=False),
        sa.Column('author_id', sa.UUID(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['copy_id'], ['book_copies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('copy_discussions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_copy_discussions_copy_id'), ['copy_id'], unique=False)

    op.create_table('pass_listings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('copy_id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('listing_type', sa.Enum('resale', 'exchange', 'lend', 'free_pass', name='passtype'), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('open', 'claimed', 'closed', 'cancelled', name='passstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['copy_id'], ['book_copies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('pass_listings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pass_listings_copy_id'), ['copy_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pass_listings_owner_id'), ['owner_id'], unique=False)

    op.create_table('pass_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('listing_id', sa.UUID(), nullable=False),
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'cancelled', name='passrequeststatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['pass_listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('pass_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pass_requests_listing_id'), ['listing_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pass_requests_requester_id'), ['requester_id'], unique=False)

    op.create_table('sos_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('urgency_hours', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('open', 'fulfilled', 'closed', 'cancelled', name='sosstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('sos_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sos_requests_requester_id'), ['requester_id'], unique=False)

    op.create_table('sos_offers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sos_id', sa.UUID(), nullable=False),
        sa.Column('offerer_id', sa.UUID(), nullable=False),
        sa.Column('copy_id', sa.UUID(), nullable=True),
        sa.Column('pass_listing_id', sa.UUID(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'cancelled', name='sosofferstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['copy_id'], ['book_copies.id']),
        sa.ForeignKeyConstraint(['offerer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pass_listing_id'], ['pass_listings.id']),
        sa.ForeignKeyConstraint(['sos_id'], ['sos_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('sos_offers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sos_offers_sos_id'), ['sos_id'], unique=False)

    op.create_table('badges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('threshold_type', sa.String(length=50), nullable=False),
        sa.Column('threshold_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_table('user_badges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('badge_id', sa.UUID(), nullable=False),
        sa.Column('awarded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge')
    )
    with op.batch_alter_table('user_badges', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_badges_user_id'), ['user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('user_badges', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_badges_user_id'))
    op.drop_table('user_badges')
    op.drop_table('badges')
    with op.batch_alter_table('sos_offers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sos_offers_sos_id'))
    op.drop_table('sos_offers')
    with op.batch_alter_table('sos_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sos_requests_requester_id'))
    op.drop_table('sos_requests')
    with op.batch_alter_table('pass_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pass_requests_requester_id'))
        batch_op.drop_index(batch_op.f('ix_pass_requests_listing_id'))
    op.drop_table('pass_requests')
    with op.batch_alter_table('pass_listings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pass_listings_owner_id'))
        batch_op.drop_index(batch_op.f('ix_pass_listings_copy_id'))
    op.drop_table('pass_listings')
    with op.batch_alter_table('copy_discussions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_copy_discussions_copy_id'))
    op.drop_table('copy_discussions')
    with op.batch_alter_table('condition_reports', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_condition_reports_copy_id'))
    op.drop_table('condition_reports')
    with op.batch_alter_table('copy_transfers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_copy_transfers_to_user_id'))
        batch_op.drop_index(batch_op.f('ix_copy_transfers_copy_id'))
    op.drop_table('copy_transfers')
    with op.batch_alter_table('book_copies', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_book_copies_source_order_id'))
        batch_op.drop_index(batch_op.f('ix_book_copies_current_owner_id'))
        batch_op.drop_index(batch_op.f('ix_book_copies_copy_code'))
        batch_op.drop_index(batch_op.f('ix_book_copies_book_id'))
    op.drop_table('book_copies')
