import random
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import or_

from app.extensions import db
from app.models import (
    Book,
    BuddyRequest,
    BuddyStatus,
    CircleClaim,
    CircleListing,
    ClaimStatus,
    DetectiveOffer,
    DetectiveOfferStatus,
    DetectiveRequest,
    DetectiveStatus,
    ListingStatus,
    Notification,
    OfferType,
    PassportEntry,
    ReaderNote,
    ReadingState,
    ReadingStatus,
    Rental,
    RentalStatus,
    SwapProposal,
    SwapStatus,
    User,
    UserInterest,
    WishStatus,
    WishlistItem,
)
from app.services.notification_service import NotificationService
from app.utils.exceptions import BadRequestError, ForbiddenError, NotFoundError


def _norm(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _uuid(value, name: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise BadRequestError(f"Invalid {name}")


def _money(value, name: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception:
        raise BadRequestError(f"Invalid {name}")
    if amount <= 0:
        raise BadRequestError(f"{name} must be greater than 0")
    return amount


def _duration_part(value, name: str, lo: int, hi: int) -> int:
    if value in (None, ""):
        return 0
    try:
        ivalue = int(value)
    except (ValueError, TypeError):
        raise BadRequestError(f"{name} must be a number")
    if ivalue < lo or ivalue > hi:
        raise BadRequestError(f"{name} must be {lo}-{hi}")
    return ivalue


def _duration_str(days: int | None, hours: int | None, mins: int | None) -> str:
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    return " ".join(parts) or "0m"


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _user_details(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "id": str(user.id),
        "name": f"{user.first_name} {user.last_name}".strip() or user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
    }


DUE_SOON_DAYS = 2


class CircleService:
    """BookCircle listings (sell/rent/donate), swaps, campus exchange, passport, fair price."""

    @staticmethod
    def create_listing(user: User, data: dict) -> CircleListing:
        try:
            offer_type = OfferType(data["offer_type"])
        except ValueError:
            raise BadRequestError(f"Invalid offer_type '{data.get('offer_type')}'")
        book_id = data.get("book_id")
        book = None
        if book_id:
            book = db.session.get(Book, book_id)
            if book is None:
                raise BadRequestError("Linked book not found")
        title = (data.get("title") or (book.title if book else "") or "").strip()
        if not title or len(title) > 255:
            raise BadRequestError("Title must be 1-255 characters")
        author = (data.get("author") or (book.author if book else None) or None)
        if author is not None:
            author = author.strip() or None
        price = rent_fee = None
        rent_days = rent_hours = rent_mins = None
        if offer_type == OfferType.sell:
            if data.get("price") in (None, ""):
                raise BadRequestError("Price is required for sell")
            price = _money(data["price"], "Price")
        elif offer_type == OfferType.rent:
            if data.get("rent_fee") in (None, ""):
                raise BadRequestError("rent_fee is required for rent")
            rent_fee = _money(data["rent_fee"], "rent_fee")
            rent_days = _duration_part(data.get("rent_days"), "rent_days", 0, 365)
            rent_hours = _duration_part(data.get("rent_hours"), "rent_hours", 0, 23)
            rent_mins = _duration_part(data.get("rent_mins"), "rent_mins", 0, 59)
            if (rent_days or 0) + (rent_hours or 0) + (rent_mins or 0) <= 0:
                raise BadRequestError("Rental duration must be at least 1 minute (days / hours / mins)")
        listing = CircleListing(
            owner_id=user.id,
            book_id=book.id if book else None,
            title=title,
            author=author,
            offer_type=offer_type,
            price=price,
            rent_fee=rent_fee,
            rent_days=rent_days,
            rent_hours=rent_hours,
            rent_mins=rent_mins,
            description=(data.get("description") or "").strip() or None,
            city=(data.get("city") or "").strip() or None,
            campus=(data.get("campus") or "").strip() or None,
            status=ListingStatus.open,
        )
        db.session.add(listing)
        db.session.commit()
        return listing

    @staticmethod
    def list_open(offer_type=None, city=None, campus=None, q=None) -> list[CircleListing]:
        query = CircleListing.query.filter_by(status=ListingStatus.open)
        if offer_type:
            try:
                query = query.filter_by(offer_type=OfferType(offer_type))
            except ValueError:
                raise BadRequestError(f"Invalid offer_type '{offer_type}'")
        if city:
            query = query.filter(CircleListing.city.ilike(f"%{city.strip()}%"))
        if campus:
            query = query.filter(CircleListing.campus.ilike(f"%{campus.strip()}%"))
        if q:
            like = f"%{q.strip()}%"
            query = query.filter(or_(CircleListing.title.ilike(like), CircleListing.author.ilike(like)))
        return query.order_by(CircleListing.created_at.desc()).limit(100).all()

    @staticmethod
    def mine(user_id: uuid.UUID) -> list[CircleListing]:
        return CircleListing.query.filter_by(owner_id=user_id).order_by(CircleListing.created_at.desc()).limit(100).all()

    @staticmethod
    def get(listing_id: uuid.UUID) -> CircleListing:
        listing = db.session.get(CircleListing, listing_id)
        if listing is None:
            raise NotFoundError("Listing not found")
        return listing

    @staticmethod
    def close(user: User, listing_id: uuid.UUID, to_status: str = "closed") -> CircleListing:
        listing = CircleService.get(listing_id)
        if listing.owner_id != user.id:
            raise ForbiddenError("Only the owner can close this listing")
        try:
            target = ListingStatus(to_status)
        except ValueError:
            raise BadRequestError(f"Invalid status '{to_status}'")
        if target not in (ListingStatus.closed, ListingStatus.cancelled):
            raise BadRequestError("Can only close or cancel")
        if listing.status != ListingStatus.open:
            raise BadRequestError("Listing is not open")
        listing.status = target
        db.session.commit()
        return listing

    @staticmethod
    def claim(user: User, listing_id: uuid.UUID, message: str | None) -> CircleClaim:
        listing = CircleService.get(listing_id)
        if listing.status != ListingStatus.open:
            raise BadRequestError("Listing is not open")
        if listing.owner_id == user.id:
            raise BadRequestError("You cannot claim your own listing")
        pending = CircleClaim.query.filter_by(listing_id=listing.id, requester_id=user.id, status=ClaimStatus.pending).first()
        if pending:
            raise BadRequestError("You already have a pending claim for this listing")
        claim = CircleClaim(listing_id=listing.id, requester_id=user.id, message=(message or "").strip() or None, status=ClaimStatus.pending)
        db.session.add(claim)
        requester_name = f"{user.first_name} {user.last_name}".strip() or user.email
        if listing.offer_type == OfferType.rent:
            NotificationService.notify(
                listing.owner_id, "rent_request",
                f"New rent request for '{listing.title}'",
                f"{requester_name} wants to rent your book for {_duration_str(listing.rent_days, listing.rent_hours, listing.rent_mins)}.",
                link="/circle", ref_type="claim", ref_id=claim.id,
            )
        else:
            NotificationService.notify(
                listing.owner_id, "claim_received",
                f"New claim for '{listing.title}'",
                f"{requester_name} claimed your {listing.offer_type.value} listing.",
                link="/circle", ref_type="claim", ref_id=claim.id,
            )
        db.session.commit()
        return claim

    @staticmethod
    def claims_for(user: User, listing_id: uuid.UUID) -> list[CircleClaim]:
        listing = CircleService.get(listing_id)
        if listing.owner_id != user.id:
            raise ForbiddenError("Only the owner can view claims")
        return CircleClaim.query.filter_by(listing_id=listing.id).order_by(CircleClaim.created_at.desc()).all()

    @staticmethod
    def accept_claim(user: User, claim_id: uuid.UUID) -> CircleClaim:
        claim = db.session.get(CircleClaim, claim_id)
        if claim is None:
            raise NotFoundError("Claim not found")
        listing = CircleService.get(claim.listing_id)
        if listing.owner_id != user.id:
            raise ForbiddenError("Only the owner can accept claims")
        if claim.status != ClaimStatus.pending or listing.status != ListingStatus.open:
            raise BadRequestError("Claim is no longer actionable")
        claim.status = ClaimStatus.accepted
        listing.status = ListingStatus.claimed
        for other in CircleClaim.query.filter_by(listing_id=listing.id, status=ClaimStatus.pending).all():
            if other.id != claim.id:
                other.status = ClaimStatus.declined
        db.session.add(PassportEntry(
            book_id=listing.book_id, title=listing.title, author=listing.author,
            from_user_id=user.id, to_user_id=claim.requester_id, listing_id=listing.id,
            note=f"BookCircle {listing.offer_type.value} claim",
        ))
        if listing.offer_type == OfferType.rent:
            now = datetime.now(timezone.utc)
            duration = _duration_str(listing.rent_days, listing.rent_hours, listing.rent_mins)
            rental = Rental(
                listing_id=listing.id,
                claim_id=claim.id,
                owner_id=user.id,
                renter_id=claim.requester_id,
                start_date=now,
                due_date=now + timedelta(
                    days=listing.rent_days or 0,
                    hours=listing.rent_hours or 0,
                    minutes=listing.rent_mins or 0,
                ),
                status=RentalStatus.active,
            )
            db.session.add(rental)
            db.session.flush()
            due_str = rental.due_date.strftime("%d %b %Y %H:%M")
            renter = db.session.get(User, claim.requester_id)
            owner = db.session.get(User, user.id)
            renter_details = _user_details(renter) or {}
            owner_details = _user_details(owner) or {}
            rent_amount = RentalService._money(listing.rent_fee)
            NotificationService.notify(
                claim.requester_id, "rent_accepted",
                f"Rent accepted for '{listing.title}'",
                f"You took '{listing.title}' from {owner_details.get('name', 'the owner')}. Return by {due_str} ({duration}). Rent to pay: ₹{rent_amount}; late penalty: 10% per full overdue day. Owner contact: {owner_details.get('phone') or 'not provided'}; handover address: {owner_details.get('address') or 'not provided'}.",
                link="/rentals", ref_type="rental", ref_id=rental.id,
            )
            NotificationService.notify(
                user.id, "rental_started",
                f"Rental started for '{listing.title}'",
                f"{renter_details.get('name', 'The renter')} took '{listing.title}' until {due_str} ({duration}). Expected rent: ₹{rent_amount}. Renter phone: {renter_details.get('phone') or 'not provided'}; renter address: {renter_details.get('address') or 'not provided'}. You will receive 1-day and 1-hour reminders.",
                link="/rentals", ref_type="rental", ref_id=rental.id,
            )
        else:
            NotificationService.notify(
                claim.requester_id, "claim_accepted",
                f"Claim accepted for '{listing.title}'",
                "The owner accepted your claim. Arrange pickup with them.",
                link="/circle", ref_type="claim", ref_id=claim.id,
            )
        db.session.commit()
        return claim

    @staticmethod
    def decline_claim(user: User, claim_id: uuid.UUID) -> CircleClaim:
        claim = db.session.get(CircleClaim, claim_id)
        if claim is None:
            raise NotFoundError("Claim not found")
        listing = CircleService.get(claim.listing_id)
        if listing.owner_id != user.id:
            raise ForbiddenError("Only the owner can decline claims")
        if claim.status != ClaimStatus.pending:
            raise BadRequestError("Claim is no longer pending")
        claim.status = ClaimStatus.declined
        NotificationService.notify(
            claim.requester_id, "claim_declined",
            f"Claim declined for '{listing.title}'",
            "The owner declined your claim. Try another listing.",
            link="/circle", ref_type="claim", ref_id=claim.id,
        )
        db.session.commit()
        return claim

    # ---- Book Swap (money-free exchange) ----

    @staticmethod
    def propose_swap(user: User, wanted_id: uuid.UUID, offered_id: uuid.UUID, message: str | None) -> SwapProposal:
        wanted = CircleService.get(wanted_id)
        offered = CircleService.get(offered_id)
        if wanted.status != ListingStatus.open or offered.status != ListingStatus.open:
            raise BadRequestError("Both listings must be open")
        if wanted.offer_type != OfferType.exchange or offered.offer_type != OfferType.exchange:
            raise BadRequestError("Swap needs exchange listings on both sides (money-free)")
        if offered.owner_id != user.id:
            raise BadRequestError("You can only offer your own listing")
        if wanted.owner_id == user.id:
            raise BadRequestError("You cannot swap with yourself")
        pending = SwapProposal.query.filter_by(
            wanted_listing_id=wanted.id, offered_listing_id=offered.id, status=SwapStatus.pending
        ).first()
        if pending:
            raise BadRequestError("A pending swap already exists between these listings")
        prop = SwapProposal(wanted_listing_id=wanted.id, offered_listing_id=offered.id, proposer_id=user.id, message=(message or "").strip() or None, status=SwapStatus.pending)
        db.session.add(prop)
        db.session.flush()
        proposer_name = f"{user.first_name} {user.last_name}".strip() or user.email
        NotificationService.notify(
            wanted.owner_id, "swap_proposed",
            f"Swap offer for '{wanted.title}'",
            f"{proposer_name} offers '{offered.title}' in exchange (no money).",
            link="/circle", ref_type="swap", ref_id=prop.id,
        )
        db.session.commit()
        return prop

    @staticmethod
    def swaps_for(user: User, listing_id: uuid.UUID) -> list[SwapProposal]:
        listing = CircleService.get(listing_id)
        if listing.owner_id != user.id:
            raise ForbiddenError("Only the owner can view swap proposals")
        return SwapProposal.query.filter_by(wanted_listing_id=listing.id).order_by(SwapProposal.created_at.desc()).all()

    @staticmethod
    def accept_swap(user: User, proposal_id: uuid.UUID) -> SwapProposal:
        prop = db.session.get(SwapProposal, proposal_id)
        if prop is None:
            raise NotFoundError("Swap proposal not found")
        wanted = CircleService.get(prop.wanted_listing_id)
        offered = CircleService.get(prop.offered_listing_id)
        if wanted.owner_id != user.id:
            raise ForbiddenError("Only the wanted-book owner can accept")
        if prop.status != SwapStatus.pending or wanted.status != ListingStatus.open or offered.status != ListingStatus.open:
            raise BadRequestError("Swap is no longer actionable")
        prop.status = SwapStatus.accepted
        wanted.status = ListingStatus.claimed
        offered.status = ListingStatus.claimed
        db.session.add(PassportEntry(book_id=wanted.book_id, title=wanted.title, author=wanted.author, from_user_id=wanted.owner_id, to_user_id=prop.proposer_id, listing_id=wanted.id, note="Book swap"))
        db.session.add(PassportEntry(book_id=offered.book_id, title=offered.title, author=offered.author, from_user_id=prop.proposer_id, to_user_id=wanted.owner_id, listing_id=offered.id, note="Book swap"))
        for other in SwapProposal.query.filter_by(wanted_listing_id=wanted.id, status=SwapStatus.pending).all():
            if other.id != prop.id:
                other.status = SwapStatus.declined
        NotificationService.notify(
            prop.proposer_id, "swap_decided",
            f"Swap accepted for '{wanted.title}'",
            "The owner accepted your swap. Arrange the exchange.",
            link="/circle", ref_type="swap", ref_id=prop.id,
        )
        db.session.commit()
        return prop

    @staticmethod
    def decline_swap(user: User, proposal_id: uuid.UUID) -> SwapProposal:
        prop = db.session.get(SwapProposal, proposal_id)
        if prop is None:
            raise NotFoundError("Swap proposal not found")
        wanted = CircleService.get(prop.wanted_listing_id)
        if wanted.owner_id != user.id:
            raise ForbiddenError("Only the wanted-book owner can decline")
        if prop.status != SwapStatus.pending:
            raise BadRequestError("Swap is no longer pending")
        prop.status = SwapStatus.declined
        NotificationService.notify(
            prop.proposer_id, "swap_decided",
            f"Swap declined for '{wanted.title}'",
            "The owner declined your swap proposal.",
            link="/circle", ref_type="swap", ref_id=prop.id,
        )
        db.session.commit()
        return prop

    # ---- Book Passport (second-hand ownership history) ----

    @staticmethod
    def passport(book_id=None, title: str | None = None, author: str | None = None) -> dict:
        entries: list[PassportEntry] = []
        book = None
        if book_id:
            bid = _uuid(book_id, "book_id")
            book = db.session.get(Book, bid)
            entries = PassportEntry.query.filter_by(book_id=bid).order_by(PassportEntry.created_at.asc()).all()
        elif title:
            norm = _norm(title)
            anorm = _norm(author)
            all_entries = PassportEntry.query.order_by(PassportEntry.created_at.asc()).all()
            entries = [e for e in all_entries if _norm(e.title) == norm and (not anorm or _norm(e.author) == anorm)]
        else:
            raise BadRequestError("Provide book_id or title")
        readers = {e.to_user_id for e in entries}
        if entries and entries[0].from_user_id:
            readers.add(entries[0].from_user_id)
        return {
            "book": book.to_dict() if book else None,
            "stamps": [e.to_dict() for e in entries],
            "reader_count": len(readers),
            "transfer_count": len(entries),
        }

    # ---- Fair Price Calculator ----

    CONDITIONS = {"new": 0.9, "like_new": 0.75, "good": 0.6, "fair": 0.45, "poor": 0.3}

    @staticmethod
    def suggest_price(book_id=None, original_price=None, condition: str = "good", age_years: int = 0, edition: str | None = None) -> dict:
        if condition not in CircleService.CONDITIONS:
            raise BadRequestError("condition must be one of: new, like_new, good, fair, poor.")
        base = None
        book = None
        if original_price not in (None, ""):
            base = _money(original_price, "original_price")
        if book_id:
            bid = _uuid(book_id, "book_id")
            book = db.session.get(Book, bid)
            if book is None:
                raise BadRequestError("Book not found")
            if base is None:
                base = book.price
        if base is None:
            raise BadRequestError("Provide book_id or original_price")
        try:
            age = int(age_years or 0)
        except (ValueError, TypeError):
            raise BadRequestError("age_years must be a number")
        if age < 0 or age > 100:
            raise BadRequestError("age_years must be 0-100")
        cond_factor = CircleService.CONDITIONS[condition]
        age_factor = max(0.5, 1 - 0.05 * age)
        edition_bonus = 1.1 if edition and "latest" in edition.lower() else 1.0
        suggested = max(Decimal("10.00"), (base * Decimal(str(cond_factor)) * Decimal(str(age_factor)) * Decimal(str(edition_bonus))).quantize(Decimal("0.01")))
        return {
            "suggested_price": str(suggested),
            "breakdown": {
                "base_price": str(base),
                "condition": condition,
                "condition_factor": cond_factor,
                "age_years": age,
                "age_factor": round(age_factor, 2),
                "edition": edition,
                "edition_factor": edition_bonus,
            },
            "book": book.to_dict() if book else None,
        }


class CommunityService:
    """Study buddy, detective, mystery match, notes, wishlist."""

    # ---- Study Buddy Match ----

    @staticmethod
    def mark_reading(user: User, data: dict) -> ReadingStatus:
        book_id = data.get("book_id")
        book = None
        if book_id:
            book = db.session.get(Book, _uuid(book_id, "book_id"))
            if book is None:
                raise BadRequestError("Book not found")
        title = (data.get("title") or (book.title if book else "") or "").strip()
        if not title or len(title) > 255:
            raise BadRequestError("Title must be 1-255 characters")
        try:
            state = ReadingState(data.get("state", "reading"))
        except ValueError:
            raise BadRequestError("state must be reading or finished")
        # one row per user+book: replace existing
        key_title, key_author = _norm(title), _norm(data.get("author") or (book.author if book else ""))
        for old in ReadingStatus.query.filter_by(user_id=user.id).all():
            if _norm(old.title) == key_title and _norm(old.author) == key_author:
                db.session.delete(old)
        row = ReadingStatus(
            user_id=user.id, book_id=book.id if book else None, title=title,
            author=((data.get("author") or (book.author if book else "") or "").strip() or None),
            state=state, city=(data.get("city") or "").strip() or None,
            campus=(data.get("campus") or "").strip() or None,
        )
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def my_reading(user_id: uuid.UUID) -> list[ReadingStatus]:
        return ReadingStatus.query.filter_by(user_id=user_id).order_by(ReadingStatus.updated_at.desc()).limit(50).all()

    @staticmethod
    def buddies_for(user: User, reading_id: uuid.UUID) -> list[dict]:
        mine = db.session.get(ReadingStatus, reading_id)
        if mine is None or mine.user_id != user.id:
            raise NotFoundError("Reading entry not found")
        key_t, key_a = _norm(mine.title), _norm(mine.author)
        out = []
        for other in ReadingStatus.query.filter(ReadingStatus.user_id != user.id, ReadingStatus.state == ReadingState.reading).limit(200).all():
            same = (mine.book_id and other.book_id == mine.book_id) or (_norm(other.title) == key_t and (not key_a or _norm(other.author) == key_a))
            if same:
                d = other.to_dict()
                u = db.session.get(User, other.user_id)
                if u:
                    d["reader"] = {"first_name": u.first_name, "last_name": u.last_name}
                out.append(d)
        return out

    @staticmethod
    def buddy_request(user: User, target_id: uuid.UUID, message: str | None):
        if target_id == user.id:
            raise BadRequestError("You cannot buddy-request yourself")
        target = db.session.get(User, target_id)
        if target is None or not target.is_active:
            raise BadRequestError("User not found")
        pending = BuddyRequest.query.filter_by(requester_id=user.id, target_id=target_id, status=BuddyStatus.pending).first()
        if pending:
            raise BadRequestError("Buddy request already pending")
        req = BuddyRequest(requester_id=user.id, target_id=target_id, message=(message or "").strip() or None, status=BuddyStatus.pending)
        db.session.add(req)
        db.session.flush()
        requester_name = f"{user.first_name} {user.last_name}".strip() or user.email
        NotificationService.notify(
            target_id, "buddy_request",
            f"Study buddy invite from {requester_name}",
            "Someone reading the same book wants to connect.",
            link="/buddy", ref_type="buddy_request", ref_id=req.id,
        )
        db.session.commit()
        return req

    @staticmethod
    def buddy_inbox(user: User) -> list[BuddyRequest]:
        reqs = BuddyRequest.query.filter_by(target_id=user.id).order_by(BuddyRequest.created_at.desc()).limit(100).all()
        for r in reqs:
            r.requester = db.session.get(User, r.requester_id)
        return reqs

    @staticmethod
    def buddy_decide(user: User, req_id: uuid.UUID, accept: bool) -> BuddyRequest:
        req = db.session.get(BuddyRequest, req_id)
        if req is None:
            raise NotFoundError("Buddy request not found")
        if req.target_id != user.id:
            raise ForbiddenError("Only the invited user can decide")
        if req.status != BuddyStatus.pending:
            raise BadRequestError("Request is no longer pending")
        req.status = BuddyStatus.accepted if accept else BuddyStatus.declined
        NotificationService.notify(
            req.requester_id, "buddy_decided",
            f"Buddy request {'accepted' if accept else 'declined'}",
            "You can now study together." if accept else "They declined your buddy request.",
            link="/buddy", ref_type="buddy_request", ref_id=req.id,
        )
        db.session.commit()
        return req

    # ---- Book Detective (rare/old book requests) ----

    @staticmethod
    def detective_create(user: User, data: dict) -> DetectiveRequest:
        title = (data.get("title") or "").strip()
        if not title or len(title) > 255:
            raise BadRequestError("Title must be 1-255 characters")
        max_price = None
        if data.get("max_price") not in (None, ""):
            max_price = _money(data["max_price"], "max_price")
        req = DetectiveRequest(
            requester_id=user.id, title=title,
            author=(data.get("author") or "").strip() or None,
            max_price=max_price, city=(data.get("city") or "").strip() or None,
            note=(data.get("note") or "").strip() or None, status=DetectiveStatus.open,
        )
        db.session.add(req)
        db.session.commit()
        return req

    @staticmethod
    def detective_list(status=None, city=None, q=None) -> list[DetectiveRequest]:
        query = DetectiveRequest.query
        if status:
            try:
                query = query.filter_by(status=DetectiveStatus(status))
            except ValueError:
                raise BadRequestError(f"Invalid status '{status}'")
        else:
            query = query.filter_by(status=DetectiveStatus.open)
        if city:
            query = query.filter(DetectiveRequest.city.ilike(f"%{city.strip()}%"))
        if q:
            like = f"%{q.strip()}%"
            query = query.filter(or_(DetectiveRequest.title.ilike(like), DetectiveRequest.author.ilike(like)))
        return query.order_by(DetectiveRequest.created_at.desc()).limit(100).all()

    @staticmethod
    def detective_offer(user: User, req_id: uuid.UUID, data: dict) -> DetectiveOffer:
        req = db.session.get(DetectiveRequest, req_id)
        if req is None:
            raise NotFoundError("Detective request not found")
        if req.status != DetectiveStatus.open:
            raise BadRequestError("Request is not open")
        if req.requester_id == user.id:
            raise BadRequestError("You cannot offer on your own request")
        book_id = None
        if data.get("book_id"):
            book = db.session.get(Book, _uuid(data["book_id"], "book_id"))
            if book is None:
                raise BadRequestError("Book not found")
            book_id = book.id
        price = None
        if data.get("price") not in (None, ""):
            price = _money(data["price"], "price")
        offer = DetectiveOffer(request_id=req.id, offerer_id=user.id, book_id=book_id, price=price, message=(data.get("message") or "").strip() or None, status=DetectiveOfferStatus.pending)
        db.session.add(offer)
        db.session.flush()
        NotificationService.notify(
            req.requester_id, "detective_offer",
            f"Offer found for '{req.title}'",
            "A seller responded to your detective request.",
            link="/detective", ref_type="detective_offer", ref_id=offer.id,
        )
        db.session.commit()
        return offer

    @staticmethod
    def detective_offers_for(user: User, req_id: uuid.UUID) -> list[DetectiveOffer]:
        req = db.session.get(DetectiveRequest, req_id)
        if req is None:
            raise NotFoundError("Detective request not found")
        if req.requester_id == user.id:
            return DetectiveOffer.query.filter_by(request_id=req.id).order_by(DetectiveOffer.created_at.desc()).all()
        mine = DetectiveOffer.query.filter_by(request_id=req.id, offerer_id=user.id).order_by(DetectiveOffer.created_at.desc()).all()
        if not mine:
            raise ForbiddenError("Only the requester and offerers can view offers")
        return mine

    @staticmethod
    def detective_accept(user: User, offer_id: uuid.UUID) -> DetectiveOffer:
        offer = db.session.get(DetectiveOffer, offer_id)
        if offer is None:
            raise NotFoundError("Offer not found")
        req = db.session.get(DetectiveRequest, offer.request_id)
        if req.requester_id != user.id:
            raise ForbiddenError("Only the requester can accept")
        if offer.status != DetectiveOfferStatus.pending or req.status != DetectiveStatus.open:
            raise BadRequestError("Offer is no longer actionable")
        offer.status = DetectiveOfferStatus.accepted
        req.status = DetectiveStatus.fulfilled
        for o in DetectiveOffer.query.filter_by(request_id=req.id, status=DetectiveOfferStatus.pending).all():
            if o.id != offer.id:
                o.status = DetectiveOfferStatus.declined
        NotificationService.notify(
            offer.offerer_id, "detective_accepted",
            f"Your offer for '{req.title}' was accepted",
            "The requester accepted your detective offer.",
            link="/detective", ref_type="detective_offer", ref_id=offer.id,
        )
        db.session.commit()
        return offer

    # ---- Mystery Book Match ----

    @staticmethod
    def save_interests(user: User, data: dict) -> UserInterest:
        row = UserInterest.query.filter_by(user_id=user.id).first()
        if row is None:
            row = UserInterest(user_id=user.id)
            db.session.add(row)
        row.genres = (data.get("genres") or "").strip() or None
        row.favorite_authors = (data.get("favorite_authors") or "").strip() or None
        row.note = (data.get("note") or "").strip() or None
        db.session.commit()
        return row

    @staticmethod
    def mystery_match(user: User) -> dict:
        interests = UserInterest.query.filter_by(user_id=user.id).first()
        from app.models import BookStatus

        catalog = Book.query.filter_by(status=BookStatus.active).filter(Book.stock > 0).all()
        if not catalog:
            raise NotFoundError("No books available for a surprise match right now")
        genres = [g.strip().lower() for g in (interests.genres.split(",") if interests and interests.genres else []) if g.strip()]
        authors = [a.strip().lower() for a in (interests.favorite_authors.split(",") if interests and interests.favorite_authors else []) if a.strip()]
        scored = []
        for b in catalog:
            score, terms = 0, []
            hay = f"{b.title} {b.author} {b.description or ''}".lower()
            for a in authors:
                if a and a in hay:
                    score += 3
                    terms.append(a)
            for g in genres:
                if g and g in hay:
                    score += 2
                    terms.append(g)
            scored.append((score, b, terms))
        best_score = max(s for s, _, _ in scored)
        top = [(b, t) for s, b, t in scored if s == best_score]
        pick, terms = random.choice(top)
        reason = f"Matched your interests: {', '.join(terms)}" if terms else "A surprise pick from the catalog"
        return {"book": pick.to_dict(include_seller=True), "reason": reason, "matched_terms": terms}

    # ---- Reader Notes ----

    @staticmethod
    def add_note(user: User, data: dict) -> ReaderNote:
        book_id = None
        book = None
        if data.get("book_id"):
            book = db.session.get(Book, _uuid(data["book_id"], "book_id"))
            if book is None:
                raise BadRequestError("Book not found")
            book_id = book.id
        title = (data.get("title") or (book.title if book else "") or "").strip() or None
        if not book_id and not title:
            raise BadRequestError("Provide book_id or title")
        text = (data.get("note") or "").strip()
        if not text or len(text) > 2000:
            raise BadRequestError("Note must be 1-2000 characters")
        row = ReaderNote(book_id=book_id, title=title, author=(data.get("author") or (book.author if book else "") or "").strip() or None, writer_id=user.id, note=text)
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def notes_for(book_id=None, title: str | None = None) -> list[ReaderNote]:
        if book_id:
            bid = _uuid(book_id, "book_id")
            return ReaderNote.query.filter_by(book_id=bid).order_by(ReaderNote.created_at.desc()).limit(100).all()
        if title:
            return ReaderNote.query.filter(ReaderNote.title.ilike(f"%{title.strip()}%")).order_by(ReaderNote.created_at.desc()).limit(100).all()
        raise BadRequestError("Provide book_id or title")

    @staticmethod
    def delete_note(user: User, note_id: uuid.UUID) -> None:
        row = db.session.get(ReaderNote, note_id)
        if row is None:
            raise NotFoundError("Note not found")
        if row.writer_id != user.id:
            raise ForbiddenError("You can only delete your own notes")
        db.session.delete(row)
        db.session.commit()

    # ---- Community Wishlist (bulk) ----

    BULK_MIN = 3

    @staticmethod
    def wish_add(user: User, data: dict) -> WishlistItem:
        title = (data.get("title") or "").strip()
        book = None
        if data.get("book_id"):
            book = db.session.get(Book, _uuid(data["book_id"], "book_id"))
            if book is None:
                raise BadRequestError("Book not found")
            if not title:
                title = book.title
        if not title or len(title) > 255:
            raise BadRequestError("Title must be 1-255 characters")
        max_price = None
        if data.get("max_price") not in (None, ""):
            max_price = _money(data["max_price"], "max_price")
        item = WishlistItem(
            user_id=user.id, book_id=book.id if book else None, title=title,
            author=(data.get("author") or (book.author if book else "") or "").strip() or None,
            city=(data.get("city") or "").strip() or None, campus=(data.get("campus") or "").strip() or None,
            max_price=max_price, status=WishStatus.open,
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def wish_groups() -> list[dict]:
        items = WishlistItem.query.filter_by(status=WishStatus.open).order_by(WishlistItem.created_at.asc()).all()
        groups: dict[tuple, dict] = {}
        for it in items:
            key = (_norm(it.title), _norm(it.author))
            g = groups.setdefault(key, {"title": it.title, "author": it.author, "count": 0, "members": [], "sample": None})
            g["count"] += 1
            g["members"].append({"user_id": str(it.user_id), "city": it.city, "campus": it.campus, "created_at": it.created_at.isoformat()})
            if g["sample"] is None:
                g["sample"] = it.to_dict()
        out = []
        for g in groups.values():
            g["bulk_eligible"] = g["count"] >= CommunityService.BULK_MIN
            g["bulk_min"] = CommunityService.BULK_MIN
            out.append(g)
        return sorted(out, key=lambda g: g["count"], reverse=True)

    @staticmethod
    def wish_mine(user_id: uuid.UUID) -> list[WishlistItem]:
        return WishlistItem.query.filter_by(user_id=user_id).order_by(WishlistItem.created_at.desc()).limit(100).all()

    @staticmethod
    def wish_close(user: User, item_id: uuid.UUID, to_status: str = "closed") -> WishlistItem:
        item = db.session.get(WishlistItem, item_id)
        if item is None:
            raise NotFoundError("Wishlist item not found")
        if item.user_id != user.id:
            raise ForbiddenError("Only the owner can update this wish")
        try:
            target = WishStatus(to_status)
        except ValueError:
            raise BadRequestError(f"Invalid status '{to_status}'")
        if target not in (WishStatus.fulfilled, WishStatus.closed, WishStatus.cancelled):
            raise BadRequestError("Can only fulfill, close or cancel")
        item.status = target
        db.session.commit()
        return item


class RentalService:
    """Rentals created when a rent claim is accepted. Return + due reminders."""

    @staticmethod
    def _money(value: Decimal | None) -> str:
        return f"{Decimal(str(value or 0)).quantize(Decimal('0.01')):.2f}"

    @staticmethod
    def _financials(rental: Rental, listing: CircleListing | None, now: datetime) -> dict:
        due = _aware(rental.due_date)
        rent_fee = Decimal(str(listing.rent_fee or 0)) if listing else Decimal("0")
        overdue_days = max(0, (now - due).days) if due and now > due else 0
        calculated_fine = (rent_fee * Decimal("0.10") * overdue_days).quantize(Decimal("0.01"))
        recorded_fine = Decimal(str(rental.fine_amount or 0))
        fine_due = max(recorded_fine, calculated_fine)
        amount_due = (rent_fee + fine_due).quantize(Decimal("0.01"))
        remaining_seconds = max(0, int((due - now).total_seconds())) if due and now < due else 0
        if due and now < due:
            total_minutes = remaining_seconds // 60
            days, remainder = divmod(total_minutes, 1440)
            hours, minutes = divmod(remainder, 60)
            parts = []
            if days:
                parts.append(f"{days}d")
            if hours:
                parts.append(f"{hours}h")
            if minutes or not parts:
                parts.append(f"{minutes}m")
            time_remaining = " ".join(parts)
        elif due:
            time_remaining = "Time completed"
        else:
            time_remaining = None
        return {
            "overdue_days": overdue_days,
            "fine_preview": RentalService._money(calculated_fine),
            "fine_due": RentalService._money(fine_due),
            "amount_due": RentalService._money(amount_due),
            "amount_to_pay": RentalService._money(amount_due),
            "amount_to_collect": RentalService._money(amount_due),
            "remaining_seconds": remaining_seconds,
            "time_remaining": time_remaining,
        }

    @staticmethod
    def _serialize(rental: Rental) -> dict:
        data = rental.to_dict()
        listing = db.session.get(CircleListing, rental.listing_id)
        if listing is not None:
            data["listing"] = listing.to_dict()
            data["duration"] = _duration_str(listing.rent_days, listing.rent_hours, listing.rent_mins)
        else:
            data["duration"] = None
        renter = db.session.get(User, rental.renter_id)
        data["renter"] = _user_details(renter)
        owner = db.session.get(User, rental.owner_id)
        data["owner"] = _user_details(owner)
        claim = db.session.get(CircleClaim, rental.claim_id)
        data["claim"] = (
            {"id": str(claim.id), "created_at": claim.created_at.isoformat(), "message": claim.message}
            if claim else None
        )
        now = datetime.now(timezone.utc)
        due = _aware(rental.due_date)
        financials = RentalService._financials(rental, listing, now)
        data.update(financials)
        data["days_left"] = (due.date() - now.date()).days if due and rental.status != RentalStatus.returned else None
        data["is_overdue"] = bool(due and now > due and rental.status != RentalStatus.returned)
        data["hours_left"] = (financials["remaining_seconds"] // 3600) if due and now < due else (0 if due else None)
        data["minutes_left"] = (financials["remaining_seconds"] // 60) if due and now < due else (0 if due else None)
        # Client details for display
        data["book_name"] = listing.title if listing else "Unknown Book"
        data["book_author"] = listing.author if listing else None
        data["return_date"] = rental.due_date.isoformat() if due else None
        data["booked_at"] = rental.start_date.isoformat() if rental.start_date else None
        data["rented_from"] = listing.city if listing else None
        data["rented_campus"] = listing.campus if listing else None
        data["rent_fee"] = str(listing.rent_fee) if listing and listing.rent_fee else None
        data["rent_days"] = listing.rent_days if listing else None
        data["rent_hours"] = listing.rent_hours if listing else None
        data["rent_mins"] = listing.rent_mins if listing else None
        return data

    @staticmethod
    def _notify_once(rental: Rental, user_id: uuid.UUID, kind: str, title: str, message: str) -> None:
        existing = Notification.query.filter_by(
            user_id=user_id, kind=kind, ref_type="rental", ref_id=str(rental.id)
        ).first()
        if existing is None:
            NotificationService.notify(
                user_id, kind, title, message,
                link="/rentals", ref_type="rental", ref_id=rental.id,
            )

    @staticmethod
    def _refresh(rental: Rental) -> None:
        """Create idempotent reminders whenever rentals or notifications are opened."""
        if rental.status == RentalStatus.returned:
            return
        now = datetime.now(timezone.utc)
        due = _aware(rental.due_date)
        if due is None:
            return
        listing = db.session.get(CircleListing, rental.listing_id)
        title = listing.title if listing else "your rented book"
        due_str = due.strftime("%d %b %Y %H:%M")
        info = RentalService._financials(rental, listing, now)
        amount = info["amount_due"]
        if info["remaining_seconds"] > 0:
            if info["remaining_seconds"] <= 86400:
                RentalService._notify_once(
                    rental, rental.renter_id, "rental_due_1_day",
                    f"1 day left to return '{title}'",
                    f"Due: {due_str}. Rent: ₹{RentalService._money(listing.rent_fee if listing else 0)}. Amount to pay at return: ₹{amount}. Return before the deadline to avoid a 10% fine per full overdue day.",
                )
                RentalService._notify_once(
                    rental, rental.owner_id, "rental_due_1_day",
                    f"1 day left for '{title}' rental",
                    f"Due: {due_str}. Expected collection at return: ₹{amount} (rent ₹{RentalService._money(listing.rent_fee if listing else 0)}; current fine ₹{info['fine_due']}).",
                )
            if info["remaining_seconds"] <= 3600:
                RentalService._notify_once(
                    rental, rental.renter_id, "rental_due_1_hour",
                    f"1 hour left to return '{title}'",
                    f"Due at {due_str}. Amount to pay: ₹{amount}. Please arrange the return now to avoid an overdue fine.",
                )
                RentalService._notify_once(
                    rental, rental.owner_id, "rental_due_1_hour",
                    f"1 hour left for '{title}' rental",
                    f"Due at {due_str}. Expected collection: ₹{amount}. Prepare to confirm receipt and record payment details.",
                )
        else:
            RentalService._notify_once(
                rental, rental.renter_id, "rental_due",
                f"Return '{title}' now",
                f"The rental ended at {due_str}. Amount currently due: ₹{amount} (rent ₹{RentalService._money(listing.rent_fee if listing else 0)}; fine ₹{info['fine_due']}). Return the book now.",
            )
            RentalService._notify_once(
                rental, rental.owner_id, "rental_due",
                f"'{title}' rental has ended",
                f"The rental ended at {due_str}. Expected collection: ₹{amount}. The renter should return the book now.",
            )
            if info["overdue_days"] >= 1:
                renter_details = _user_details(db.session.get(User, rental.renter_id)) or {}
                owner_details = _user_details(db.session.get(User, rental.owner_id)) or {}
                RentalService._notify_once(
                    rental, rental.renter_id, "rental_overdue",
                    f"'{title}' is overdue",
                    f"Overdue by {info['overdue_days']} full day(s). Fine due: ₹{info['fine_due']}; total currently due: ₹{amount}. Please return it immediately.",
                )
                RentalService._notify_once(
                    rental, rental.owner_id, "rental_overdue",
                    f"'{title}' is overdue",
                    f"Overdue by {info['overdue_days']} full day(s). Fine to collect: ₹{info['fine_due']}; total expected: ₹{amount}. Please follow up with the renter.",
                )
                RentalService._notify_once(
                    rental, rental.renter_id, "rental_collection_notice",
                    f"Owner follow-up for overdue '{title}'",
                    f"The book is overdue by {info['overdue_days']} full day(s). Please return it immediately. The owner, {owner_details.get('name', 'the owner')}, may contact you at {owner_details.get('phone') or 'their saved contact'} to arrange collection. Total currently due: ₹{amount}.",
                )
                RentalService._notify_once(
                    rental, rental.owner_id, "rental_collection_notice",
                    f"Arrange collection of overdue '{title}'",
                    f"The renter, {renter_details.get('name', 'the renter')}, has not returned the book. You may contact them at {renter_details.get('phone') or 'not provided'} and arrange collection from: {renter_details.get('address') or 'address not provided'}. Total expected: ₹{amount}.",
                )
        rental.last_due_reminder_at = now

    @staticmethod
    def refresh_for_user(user: User) -> None:
        rentals = Rental.query.filter(
            or_(Rental.renter_id == user.id, Rental.owner_id == user.id),
            Rental.status != RentalStatus.returned,
        ).all()
        for rental in rentals:
            RentalService._refresh(rental)
        db.session.commit()

    @staticmethod
    def my_rentals(user: User) -> list[dict]:
        RentalService.refresh_for_user(user)
        rentals = Rental.query.filter_by(renter_id=user.id).order_by(Rental.due_date.asc()).all()
        return [RentalService._serialize(r) for r in rentals]

    @staticmethod
    def rented_out(user: User) -> list[dict]:
        RentalService.refresh_for_user(user)
        rentals = Rental.query.filter_by(owner_id=user.id).order_by(Rental.due_date.asc()).all()
        return [RentalService._serialize(r) for r in rentals]

    @staticmethod
    def get_for(user: User, rental_id: uuid.UUID) -> Rental:
        rental = db.session.get(Rental, rental_id)
        if rental is None or (rental.renter_id != user.id and rental.owner_id != user.id):
            raise NotFoundError("Rental not found")
        return rental

    @staticmethod
    def request_return(user: User, rental_id: uuid.UUID) -> Rental:
        rental = RentalService.get_for(user, rental_id)
        if rental.renter_id != user.id:
            raise ForbiddenError("Only the renter can return this book")
        if rental.status != RentalStatus.active:
            raise BadRequestError("This rental is not active")
        rental.status = RentalStatus.return_requested
        rental.return_requested_at = datetime.now(timezone.utc)
        listing = db.session.get(CircleListing, rental.listing_id)
        info = RentalService._financials(rental, listing, datetime.now(timezone.utc))
        title = listing.title if listing else "your book"
        renter_details = _user_details(db.session.get(User, rental.renter_id)) or {}
        owner_details = _user_details(db.session.get(User, rental.owner_id)) or {}
        NotificationService.notify(
            rental.owner_id, "rental_return_requested",
            f"Return requested for '{title}'",
            f"{renter_details.get('name', 'The renter')} requested return of '{title}'. Renter phone: {renter_details.get('phone') or 'not provided'}; handover address: {renter_details.get('address') or 'not provided'}. Due: {rental.due_date.strftime('%d %b %Y %H:%M')}. Rent: ₹{RentalService._money(listing.rent_fee if listing else 0)}; fine due: ₹{info['fine_due']}; total to collect: ₹{info['amount_to_collect']}. Confirm receipt and record payment details.",
            link="/rentals", ref_type="rental", ref_id=rental.id,
        )
        NotificationService.notify(
            rental.renter_id, "rental_return_requested",
            f"Return request recorded for '{title}'",
            f"Your return request was sent to {owner_details.get('name', 'the owner')}. Owner phone: {owner_details.get('phone') or 'not provided'}; handover address: {owner_details.get('address') or 'not provided'}. Amount currently due: ₹{info['amount_to_pay']} (rent ₹{RentalService._money(listing.rent_fee if listing else 0)}; fine ₹{info['fine_due']}). Keep the book ready for handover.",
            link="/rentals", ref_type="rental", ref_id=rental.id,
        )
        db.session.commit()
        return rental

    @staticmethod
    def cancel_return_request(user: User, rental_id: uuid.UUID) -> Rental:
        rental = RentalService.get_for(user, rental_id)
        if rental.renter_id != user.id:
            raise ForbiddenError("Only the renter can do this")
        if rental.status != RentalStatus.return_requested:
            raise BadRequestError("No return request to withdraw")
        rental.status = RentalStatus.active
        rental.return_requested_at = None
        listing = db.session.get(CircleListing, rental.listing_id)
        title = listing.title if listing else "your book"
        NotificationService.notify(
            rental.owner_id, "rental_return_cancelled",
            f"Return request withdrawn for '{title}'",
            "The renter withdrew the return request. The rental remains active until a new return request or the due time.",
            link="/rentals", ref_type="rental", ref_id=rental.id,
        )
        db.session.commit()
        return rental

    @staticmethod
    def confirm_return(user: User, rental_id: uuid.UUID) -> Rental:
        rental = RentalService.get_for(user, rental_id)
        if rental.owner_id != user.id:
            raise ForbiddenError("Only the owner can confirm the return")
        if rental.status not in (RentalStatus.active, RentalStatus.return_requested):
            raise BadRequestError("This rental is already closed")
        rental.status = RentalStatus.returned
        rental.returned_at = datetime.now(timezone.utc)
        listing = db.session.get(CircleListing, rental.listing_id)
        if listing is not None and listing.status == ListingStatus.claimed:
            listing.status = ListingStatus.open
        if listing is not None:
            info = RentalService._financials(rental, listing, datetime.now(timezone.utc))
            collected = RentalService._money(rental.amount_collected if rental.amount_collected is not None else info["amount_due"])
            renter_details = _user_details(db.session.get(User, rental.renter_id)) or {}
            db.session.add(PassportEntry(
                book_id=listing.book_id, title=listing.title, author=listing.author,
                from_user_id=rental.renter_id, to_user_id=rental.owner_id,
                listing_id=listing.id, note="BookCircle rent return",
            ))
            NotificationService.notify(
                rental.renter_id, "rental_returned",
                f"Return confirmed for '{listing.title}'",
                f"{renter_details.get('name', 'The renter')} returned '{listing.title}' at {rental.returned_at.strftime('%d %b %Y %H:%M')}. Expected amount: ₹{info['amount_due']}; recorded collected: ₹{collected}; fine: ₹{info['fine_due']}. Return completed.",
                link="/rentals", ref_type="rental", ref_id=rental.id,
            )
            NotificationService.notify(
                rental.owner_id, "rental_returned",
                f"Return completed for '{listing.title}'",
                f"Receipt confirmed for '{listing.title}' at {rental.returned_at.strftime('%d %b %Y %H:%M')}. Expected amount: ₹{info['amount_due']}; recorded collected: ₹{collected}; fine: ₹{info['fine_due']}. The listing is open again.",
                link="/rentals", ref_type="rental", ref_id=rental.id,
            )
        db.session.commit()
        return rental

    @staticmethod
    def complete_return_with_details(user: User, rental_id: uuid.UUID, data: dict) -> Rental:
        """Owner completes return with payment details, fine, and notes."""
        rental = RentalService.get_for(user, rental_id)
        if rental.owner_id != user.id:
            raise ForbiddenError("Only the owner can complete the return")
        if rental.status not in (RentalStatus.active, RentalStatus.return_requested):
            raise BadRequestError("This rental is already closed")

        # Update rental with payment/fine details
        if data.get("fine_amount") is not None:
            try:
                rental.fine_amount = Decimal(str(data["fine_amount"]))
            except Exception:
                raise BadRequestError("Invalid fine_amount")
        if data.get("amount_collected") is not None:
            try:
                rental.amount_collected = Decimal(str(data["amount_collected"]))
            except Exception:
                raise BadRequestError("Invalid amount_collected")
        if data.get("payment_method"):
            rental.payment_method = data["payment_method"]
        if data.get("payment_note"):
            rental.payment_note = data["payment_note"]

        rental.status = RentalStatus.returned
        rental.returned_at = datetime.now(timezone.utc)

        listing = db.session.get(CircleListing, rental.listing_id)
        if listing is not None and listing.status == ListingStatus.claimed:
            listing.status = ListingStatus.open
        if listing is not None:
            renter_details = _user_details(db.session.get(User, rental.renter_id)) or {}
            db.session.add(PassportEntry(
                book_id=listing.book_id, title=listing.title, author=listing.author,
                from_user_id=rental.renter_id, to_user_id=rental.owner_id,
                listing_id=listing.id, note="BookCircle rent return with details",
            ))
            NotificationService.notify(
                rental.renter_id, "rental_returned_with_details",
                f"Return confirmed for '{listing.title}'",
                f"{renter_details.get('name', 'The renter')} returned '{listing.title}' at {rental.returned_at.strftime('%d %b %Y %H:%M')}. Rent: ₹{RentalService._money(listing.rent_fee)}, fine: ₹{RentalService._money(rental.fine_amount)}, total expected: ₹{RentalService._money((listing.rent_fee or 0) + (rental.fine_amount or 0))}, collected: ₹{RentalService._money(rental.amount_collected)}, payment: {rental.payment_method or 'N/A'}. Note: {rental.payment_note or 'N/A'}",
                link="/rentals", ref_type="rental", ref_id=rental.id,
            )
            NotificationService.notify(
                rental.owner_id, "rental_returned_with_details",
                f"Return details saved for '{listing.title}'",
                f"Return from {renter_details.get('name', 'the renter')} recorded at {rental.returned_at.strftime('%d %b %Y %H:%M')}. Rent: ₹{RentalService._money(listing.rent_fee)}, fine: ₹{RentalService._money(rental.fine_amount)}, total expected: ₹{RentalService._money((listing.rent_fee or 0) + (rental.fine_amount or 0))}, collected: ₹{RentalService._money(rental.amount_collected)}; payment: {rental.payment_method or 'N/A'}. Note: {rental.payment_note or 'N/A'}",
                link="/rentals", ref_type="rental", ref_id=rental.id,
            )
        db.session.commit()
        return rental

    @staticmethod
    def apply_overdue_fine(user: User, rental_id: uuid.UUID) -> Rental:
        """Owner applies 10% fine per full overdue day. No fine while in time."""
        rental = RentalService.get_for(user, rental_id)
        if rental.owner_id != user.id:
            raise ForbiddenError("Only the owner can apply fines")
        if rental.status != RentalStatus.active:
            raise BadRequestError("Can only fine active rentals")

        now = datetime.now(timezone.utc)
        due = _aware(rental.due_date)
        if due is None or now <= due:
            raise BadRequestError("Rental is not overdue yet")
        overdue_days = (now - due).days
        if overdue_days < 1:
            raise BadRequestError("Fine applies only per full overdue day — no full day overdue yet")

        # 10% of rent fee per overdue day (idempotent: recomputed, not stacked)
        listing = db.session.get(CircleListing, rental.listing_id)
        rent_fee = listing.rent_fee if listing and listing.rent_fee else Decimal("0")
        fine = (rent_fee * Decimal("0.10") * overdue_days).quantize(Decimal("0.01"))
        rental.fine_amount = fine
        db.session.commit()

        NotificationService.notify(
            rental.renter_id, "rental_overdue_fined",
            f"Overdue fine for '{listing.title if listing else 'your rental'}'",
            f"{overdue_days} day(s) overdue. Fine: ₹{fine:.2f}; rent: ₹{RentalService._money(rent_fee)}; total currently due: ₹{RentalService._money(rent_fee + fine)}. Please return the book.",
            link="/rentals", ref_type="rental", ref_id=rental.id,
        )
        NotificationService.notify(
            rental.owner_id, "rental_overdue_fined",
            f"Fine updated for '{listing.title if listing else 'your rental'}'",
            f"{overdue_days} day(s) overdue. Fine to collect: ₹{fine:.2f}; rent: ₹{RentalService._money(rent_fee)}; total expected: ₹{RentalService._money(rent_fee + fine)}.",
            link="/rentals", ref_type="rental", ref_id=rental.id,
        )
        return rental

    @staticmethod
    def check_rental_completion_notifications() -> None:
        """Called when rentals are read - notify renter when rental period completes."""
        # This runs lazily when rentals are accessed
        now = datetime.now(timezone.utc)
        active_rentals = Rental.query.filter_by(status=RentalStatus.active).all()
        for rental in active_rentals:
            due = _aware(rental.due_date)
            if due is None:
                continue
            if now >= due and rental.status == RentalStatus.active:
                # Rental period completed - notify renter to return book
                listing = db.session.get(CircleListing, rental.listing_id)
                title = listing.title if listing else "your rented book"
                NotificationService.notify(
                    rental.renter_id, "rental_period_completed",
                    f"Rental period completed for '{title}'",
                    f"Your rental period has ended. Please return the book to the owner. If overdue, a 10% fine may apply.",
                    link="/rentals", ref_type="rental", ref_id=rental.id,
                )
