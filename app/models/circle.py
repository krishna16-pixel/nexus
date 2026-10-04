import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OfferType(enum.Enum):
    sell = "sell"
    rent = "rent"
    donate = "donate"
    exchange = "exchange"


class ListingStatus(enum.Enum):
    open = "open"
    claimed = "claimed"
    closed = "closed"
    cancelled = "cancelled"


class ClaimStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"


class SwapStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"


class ReadingState(enum.Enum):
    reading = "reading"
    finished = "finished"


class BuddyStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"


class DetectiveStatus(enum.Enum):
    open = "open"
    fulfilled = "fulfilled"
    closed = "closed"
    cancelled = "cancelled"


class DetectiveOfferStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"


class WishStatus(enum.Enum):
    open = "open"
    fulfilled = "fulfilled"
    closed = "closed"
    cancelled = "cancelled"


class RentalStatus(enum.Enum):
    active = "active"
    return_requested = "return_requested"
    returned = "returned"


class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ref_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ref_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_read: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "kind": self.kind,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }


class Rental(db.Model):
    __tablename__ = "rentals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("circle_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("circle_claims.id", ondelete="CASCADE"), nullable=False, unique=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    renter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    return_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_due_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fine_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    amount_collected: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RentalStatus] = mapped_column(Enum(RentalStatus), nullable=False, default=RentalStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    listing = relationship("CircleListing")

    def to_dict(self, days_left: int | None = None, is_overdue: bool = False) -> dict:
        return {
            "id": str(self.id),
            "listing_id": str(self.listing_id),
            "claim_id": str(self.claim_id),
            "owner_id": str(self.owner_id),
            "renter_id": str(self.renter_id),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
            "return_requested_at": self.return_requested_at.isoformat() if self.return_requested_at else None,
            "fine_amount": str(self.fine_amount) if self.fine_amount is not None else "0.00",
            "amount_collected": str(self.amount_collected) if self.amount_collected is not None else None,
            "payment_method": self.payment_method,
            "payment_note": self.payment_note,
            "status": self.status.value,
            "days_left": days_left,
            "is_overdue": is_overdue,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CircleListing(db.Model):
    __tablename__ = "circle_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    offer_type: Mapped[OfferType] = mapped_column(Enum(OfferType), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rent_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rent_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rent_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rent_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    campus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), nullable=False, default=ListingStatus.open)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    owner = relationship("User")
    book = relationship("Book")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "owner_id": str(self.owner_id),
            "book_id": str(self.book_id) if self.book_id else None,
            "title": self.title,
            "author": self.author,
            "offer_type": self.offer_type.value,
            "price": str(self.price) if self.price is not None else None,
            "rent_fee": str(self.rent_fee) if self.rent_fee is not None else None,
            "rent_days": self.rent_days,
            "rent_hours": self.rent_hours,
            "rent_mins": self.rent_mins,
            "description": self.description,
            "city": self.city,
            "campus": self.campus,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CircleClaim(db.Model):
    __tablename__ = "circle_claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("circle_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), nullable=False, default=ClaimStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    listing = relationship("CircleListing")
    requester = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "listing_id": str(self.listing_id),
            "requester_id": str(self.requester_id),
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SwapProposal(db.Model):
    __tablename__ = "swap_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wanted_listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("circle_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    offered_listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("circle_listings.id", ondelete="CASCADE"), nullable=False)
    proposer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SwapStatus] = mapped_column(Enum(SwapStatus), nullable=False, default=SwapStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "wanted_listing_id": str(self.wanted_listing_id),
            "offered_listing_id": str(self.offered_listing_id),
            "proposer_id": str(self.proposer_id),
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ReadingStatus(db.Model):
    __tablename__ = "reading_status"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[ReadingState] = mapped_column(Enum(ReadingState), nullable=False, default=ReadingState.reading)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    campus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    user = relationship("User")
    book = relationship("Book")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "book_id": str(self.book_id) if self.book_id else None,
            "title": self.title,
            "author": self.author,
            "state": self.state.value,
            "city": self.city,
            "campus": self.campus,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class BuddyRequest(db.Model):
    __tablename__ = "buddy_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[BuddyStatus] = mapped_column(Enum(BuddyStatus), nullable=False, default=BuddyStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    def to_dict(self) -> dict:
        data = {
            "id": str(self.id),
            "requester_id": str(self.requester_id),
            "target_id": str(self.target_id),
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }
        for attr in ("requester", "target"):
            u = getattr(self, attr, None)
            if u is not None:
                try:
                    data[attr] = {"first_name": u.first_name, "last_name": u.last_name}
                except Exception:
                    pass
        return data


BuddyRequest.requester = relationship("User", foreign_keys=[BuddyRequest.requester_id])
BuddyRequest.target = relationship("User", foreign_keys=[BuddyRequest.target_id])


class DetectiveRequest(db.Model):
    __tablename__ = "detective_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DetectiveStatus] = mapped_column(Enum(DetectiveStatus), nullable=False, default=DetectiveStatus.open)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    requester = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "requester_id": str(self.requester_id),
            "title": self.title,
            "author": self.author,
            "max_price": str(self.max_price) if self.max_price is not None else None,
            "city": self.city,
            "note": self.note,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DetectiveOffer(db.Model):
    __tablename__ = "detective_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("detective_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    offerer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DetectiveOfferStatus] = mapped_column(Enum(DetectiveOfferStatus), nullable=False, default=DetectiveOfferStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "request_id": str(self.request_id),
            "offerer_id": str(self.offerer_id),
            "book_id": str(self.book_id) if self.book_id else None,
            "price": str(self.price) if self.price is not None else None,
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }


class PassportEntry(db.Model):
    __tablename__ = "passport_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    to_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    listing_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("circle_listings.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "book_id": str(self.book_id) if self.book_id else None,
            "title": self.title,
            "author": self.author,
            "from_user_id": str(self.from_user_id) if self.from_user_id else None,
            "to_user_id": str(self.to_user_id),
            "listing_id": str(self.listing_id) if self.listing_id else None,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }


class ReaderNote(db.Model):
    __tablename__ = "reader_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    writer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    writer = relationship("User")

    def to_dict(self) -> dict:
        data = {
            "id": str(self.id),
            "book_id": str(self.book_id) if self.book_id else None,
            "title": self.title,
            "author": self.author,
            "writer_id": str(self.writer_id),
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if getattr(self, "writer", None) is not None:
            try:
                data["writer"] = {"first_name": self.writer.first_name, "last_name": self.writer.last_name}
            except Exception:
                pass
        return data


class UserInterest(db.Model):
    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_interest"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    genres: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favorite_authors: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "genres": self.genres,
            "favorite_authors": self.favorite_authors,
            "note": self.note,
        }


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    campus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[WishStatus] = mapped_column(Enum(WishStatus), nullable=False, default=WishStatus.open)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    user = relationship("User")
    book = relationship("Book")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "book_id": str(self.book_id) if self.book_id else None,
            "title": self.title,
            "author": self.author,
            "city": self.city,
            "campus": self.campus,
            "max_price": str(self.max_price) if self.max_price is not None else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
