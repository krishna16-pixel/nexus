"""Add BookCircle community tables (journey tables left dormant)

Revision ID: c4c1circle01
Revises: b7c2journey01
Create Date: 2026-09-30

Additive only — no changes to existing tables.
"""
from alembic import op
import sqlalchemy as sa


revision = 'c4c1circle01'
down_revision = 'b7c2journey01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('circle_listings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('offer_type', sa.Enum('sell', 'rent', 'donate', 'exchange', name='offertype'), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('rent_fee', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('rent_days', sa.Integer(), nullable=True),
        sa.Column('rent_hours', sa.Integer(), nullable=True),
        sa.Column('rent_mins', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('campus', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('open', 'claimed', 'closed', 'cancelled', name='listingstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('circle_listings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_circle_listings_owner_id'), ['owner_id'], unique=False)

    op.create_table('circle_claims',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('listing_id', sa.UUID(), nullable=False),
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'cancelled', name='claimstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['circle_listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('circle_claims', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_circle_claims_listing_id'), ['listing_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_circle_claims_requester_id'), ['requester_id'], unique=False)

    op.create_table('swap_proposals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('wanted_listing_id', sa.UUID(), nullable=False),
        sa.Column('offered_listing_id', sa.UUID(), nullable=False),
        sa.Column('proposer_id', sa.UUID(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'cancelled', name='swapstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['offered_listing_id'], ['circle_listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['proposer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['wanted_listing_id'], ['circle_listings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('swap_proposals', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_swap_proposals_wanted_listing_id'), ['wanted_listing_id'], unique=False)

    op.create_table('reading_status',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('state', sa.Enum('reading', 'finished', name='readingstate'), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('campus', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('reading_status', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reading_status_user_id'), ['user_id'], unique=False)

    op.create_table('buddy_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('target_id', sa.UUID(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'cancelled', name='buddystatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('buddy_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_buddy_requests_target_id'), ['target_id'], unique=False)

    op.create_table('detective_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('max_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('open', 'fulfilled', 'closed', 'cancelled', name='detectivestatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('detective_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_detective_requests_requester_id'), ['requester_id'], unique=False)

    op.create_table('detective_offers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_id', sa.UUID(), nullable=False),
        sa.Column('offerer_id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'cancelled', name='detectiveofferstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['offerer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['request_id'], ['detective_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('detective_offers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_detective_offers_request_id'), ['request_id'], unique=False)

    op.create_table('passport_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('from_user_id', sa.UUID(), nullable=True),
        sa.Column('to_user_id', sa.UUID(), nullable=False),
        sa.Column('listing_id', sa.UUID(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['listing_id'], ['circle_listings.id']),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('passport_entries', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_passport_entries_book_id'), ['book_id'], unique=False)

    op.create_table('reader_notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('writer_id', sa.UUID(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['writer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('reader_notes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reader_notes_book_id'), ['book_id'], unique=False)

    op.create_table('user_interests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('genres', sa.String(length=500), nullable=True),
        sa.Column('favorite_authors', sa.String(length=500), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_interest')
    )
    op.create_table('wishlist_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('campus', sa.String(length=255), nullable=True),
        sa.Column('max_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.Enum('open', 'fulfilled', 'closed', 'cancelled', name='wishstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('wishlist_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_wishlist_items_user_id'), ['user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('wishlist_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wishlist_items_user_id'))
    op.drop_table('wishlist_items')
    op.drop_table('user_interests')
    with op.batch_alter_table('reader_notes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reader_notes_book_id'))
    op.drop_table('reader_notes')
    with op.batch_alter_table('passport_entries', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_passport_entries_book_id'))
    op.drop_table('passport_entries')
    with op.batch_alter_table('detective_offers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_detective_offers_request_id'))
    op.drop_table('detective_offers')
    with op.batch_alter_table('detective_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_detective_requests_requester_id'))
    op.drop_table('detective_requests')
    with op.batch_alter_table('buddy_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_buddy_requests_target_id'))
    op.drop_table('buddy_requests')
    with op.batch_alter_table('reading_status', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reading_status_user_id'))
    op.drop_table('reading_status')
    with op.batch_alter_table('swap_proposals', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_swap_proposals_wanted_listing_id'))
    op.drop_table('swap_proposals')
    with op.batch_alter_table('circle_claims', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_circle_claims_requester_id'))
        batch_op.drop_index(batch_op.f('ix_circle_claims_listing_id'))
    op.drop_table('circle_claims')
    with op.batch_alter_table('circle_listings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_circle_listings_owner_id'))
    op.drop_table('circle_listings')
