from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.schemas.circle import (
    BuddyRequestSchema,
    CircleListingSchema,
    ClaimSchema,
    DetectiveOfferSchema,
    DetectiveSchema,
    InterestSchema,
    NoteSchema,
    PriceSuggestSchema,
    ReadingSchema,
    SwapSchema,
    WishSchema,
)
from app.services.circle_service import CircleService, CommunityService, RentalService
from app.services.notification_service import NotificationService
from app.utils.decorators import role_required
from app.utils.errors import error_response

circle_bp = Blueprint("circle", __name__)

listing_schema = CircleListingSchema()
claim_schema = ClaimSchema()
swap_schema = SwapSchema()
reading_schema = ReadingSchema()
buddy_schema = BuddyRequestSchema()
detective_schema = DetectiveSchema()
detective_offer_schema = DetectiveOfferSchema()
price_schema = PriceSuggestSchema()
note_schema = NoteSchema()
interest_schema = InterestSchema()
wish_schema = WishSchema()

ROLES = ("buyer", "seller")


def _load(schema, required=True):
    try:
        return schema.load(request.get_json() or {})
    except ValidationError as err:
        raise err


@circle_bp.route("/listings", methods=["POST"])
@role_required(*ROLES)
def create_listing(user):
    try:
        data = _load(listing_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    listing = CircleService.create_listing(user, data)
    return jsonify({"listing": listing.to_dict()}), 201


@circle_bp.route("/listings", methods=["GET"])
@role_required(*ROLES)
def list_listings(user):
    listings = CircleService.list_open(
        offer_type=request.args.get("type"),
        city=request.args.get("city"),
        campus=request.args.get("campus"),
        q=request.args.get("q"),
    )
    return jsonify({"listings": [x.to_dict() for x in listings], "count": len(listings)})


@circle_bp.route("/listings/mine", methods=["GET"])
@role_required(*ROLES)
def my_listings(user):
    listings = CircleService.mine(user.id)
    return jsonify({"listings": [x.to_dict() for x in listings], "count": len(listings)})


@circle_bp.route("/listings/<uuid:listing_id>", methods=["GET"])
@role_required(*ROLES)
def get_listing(user, listing_id):
    listing = CircleService.get(listing_id)
    return jsonify({"listing": listing.to_dict()})


@circle_bp.route("/listings/<uuid:listing_id>/close", methods=["PATCH"])
@role_required(*ROLES)
def close_listing(user, listing_id):
    body = request.get_json() or {}
    listing = CircleService.close(user, listing_id, body.get("status", "closed"))
    return jsonify({"listing": listing.to_dict()})


@circle_bp.route("/listings/<uuid:listing_id>/claims", methods=["POST"])
@role_required(*ROLES)
def claim_listing(user, listing_id):
    try:
        data = _load(claim_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    claim = CircleService.claim(user, listing_id, data.get("message"))
    return jsonify({"claim": claim.to_dict()}), 201


@circle_bp.route("/listings/<uuid:listing_id>/claims", methods=["GET"])
@role_required(*ROLES)
def listing_claims(user, listing_id):
    claims = CircleService.claims_for(user, listing_id)
    return jsonify({"claims": [c.to_dict() for c in claims], "count": len(claims)})


@circle_bp.route("/claims/<uuid:claim_id>/accept", methods=["POST"])
@role_required(*ROLES)
def accept_claim(user, claim_id):
    claim = CircleService.accept_claim(user, claim_id)
    return jsonify({"claim": claim.to_dict()})


@circle_bp.route("/claims/<uuid:claim_id>/decline", methods=["POST"])
@role_required(*ROLES)
def decline_claim(user, claim_id):
    claim = CircleService.decline_claim(user, claim_id)
    return jsonify({"claim": claim.to_dict()})


@circle_bp.route("/swaps", methods=["POST"])
@role_required(*ROLES)
def propose_swap(user):
    try:
        data = _load(swap_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    prop = CircleService.propose_swap(user, data["wanted_listing_id"], data["offered_listing_id"], data.get("message"))
    return jsonify({"swap": prop.to_dict()}), 201


@circle_bp.route("/listings/<uuid:listing_id>/swaps", methods=["GET"])
@role_required(*ROLES)
def listing_swaps(user, listing_id):
    props = CircleService.swaps_for(user, listing_id)
    return jsonify({"swaps": [p.to_dict() for p in props], "count": len(props)})


@circle_bp.route("/swaps/<uuid:proposal_id>/accept", methods=["POST"])
@role_required(*ROLES)
def accept_swap(user, proposal_id):
    prop = CircleService.accept_swap(user, proposal_id)
    return jsonify({"swap": prop.to_dict()})


@circle_bp.route("/swaps/<uuid:proposal_id>/decline", methods=["POST"])
@role_required(*ROLES)
def decline_swap(user, proposal_id):
    prop = CircleService.decline_swap(user, proposal_id)
    return jsonify({"swap": prop.to_dict()})


@circle_bp.route("/passport", methods=["GET"])
@role_required(*ROLES)
def passport(user):
    from uuid import UUID as _UUID

    book_id = request.args.get("book_id")
    if book_id:
        try:
            _UUID(book_id)
        except ValueError:
            return error_response("validation_error", "Invalid book_id", status_code=400)
    result = CircleService.passport(book_id=book_id, title=request.args.get("title"), author=request.args.get("author"))
    return jsonify(result)


@circle_bp.route("/price-suggest", methods=["POST"])
@role_required(*ROLES)
def price_suggest(user):
    try:
        data = _load(price_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    return jsonify(CircleService.suggest_price(
        book_id=data.get("book_id"), original_price=data.get("original_price"),
        condition=data["condition"], age_years=data.get("age_years", 0), edition=data.get("edition"),
    ))


@circle_bp.route("/reading", methods=["POST"])
@role_required(*ROLES)
def mark_reading(user):
    try:
        data = _load(reading_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    row = CommunityService.mark_reading(user, data)
    return jsonify({"reading": row.to_dict()}), 201


@circle_bp.route("/reading/mine", methods=["GET"])
@role_required(*ROLES)
def my_reading(user):
    rows = CommunityService.my_reading(user.id)
    return jsonify({"reading": [r.to_dict() for r in rows], "count": len(rows)})


@circle_bp.route("/reading/<uuid:reading_id>/buddies", methods=["GET"])
@role_required(*ROLES)
def buddies(user, reading_id):
    return jsonify({"buddies": CommunityService.buddies_for(user, reading_id)})


@circle_bp.route("/buddies/request", methods=["POST"])
@role_required(*ROLES)
def buddy_request(user):
    try:
        data = _load(buddy_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    req = CommunityService.buddy_request(user, data["target_id"], data.get("message"))
    return jsonify({"request": req.to_dict()}), 201


@circle_bp.route("/buddies/inbox", methods=["GET"])
@role_required(*ROLES)
def buddy_inbox(user):
    reqs = CommunityService.buddy_inbox(user)
    return jsonify({"requests": [r.to_dict() for r in reqs], "count": len(reqs)})


@circle_bp.route("/buddies/<uuid:req_id>/accept", methods=["POST"])
@role_required(*ROLES)
def buddy_accept(user, req_id):
    req = CommunityService.buddy_decide(user, req_id, True)
    return jsonify({"request": req.to_dict()})


@circle_bp.route("/buddies/<uuid:req_id>/decline", methods=["POST"])
@role_required(*ROLES)
def buddy_decline(user, req_id):
    req = CommunityService.buddy_decide(user, req_id, False)
    return jsonify({"request": req.to_dict()})


@circle_bp.route("/detective", methods=["POST"])
@role_required(*ROLES)
def detective_create(user):
    try:
        data = _load(detective_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    req = CommunityService.detective_create(user, data)
    return jsonify({"request": req.to_dict()}), 201


@circle_bp.route("/detective", methods=["GET"])
@role_required(*ROLES)
def detective_list(user):
    items = CommunityService.detective_list(status=request.args.get("status"), city=request.args.get("city"), q=request.args.get("q"))
    return jsonify({"requests": [x.to_dict() for x in items], "count": len(items)})


@circle_bp.route("/detective/<uuid:req_id>/offers", methods=["POST"])
@role_required(*ROLES)
def detective_offer(user, req_id):
    try:
        data = _load(detective_offer_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    offer = CommunityService.detective_offer(user, req_id, data)
    return jsonify({"offer": offer.to_dict()}), 201


@circle_bp.route("/detective/<uuid:req_id>/offers", methods=["GET"])
@role_required(*ROLES)
def detective_offers(user, req_id):
    offers = CommunityService.detective_offers_for(user, req_id)
    return jsonify({"offers": [o.to_dict() for o in offers], "count": len(offers)})


@circle_bp.route("/detective/offers/<uuid:offer_id>/accept", methods=["POST"])
@role_required(*ROLES)
def detective_accept(user, offer_id):
    offer = CommunityService.detective_accept(user, offer_id)
    return jsonify({"offer": offer.to_dict()})


@circle_bp.route("/interests", methods=["PUT"])
@role_required(*ROLES)
def save_interests(user):
    try:
        data = _load(interest_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    row = CommunityService.save_interests(user, data)
    return jsonify({"interests": row.to_dict()})


@circle_bp.route("/mystery", methods=["GET"])
@role_required(*ROLES)
def mystery(user):
    return jsonify(CommunityService.mystery_match(user))


@circle_bp.route("/notes", methods=["POST"])
@role_required(*ROLES)
def add_note(user):
    try:
        data = _load(note_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    row = CommunityService.add_note(user, data)
    return jsonify({"note": row.to_dict()}), 201


@circle_bp.route("/notes", methods=["GET"])
@role_required(*ROLES)
def list_notes(user):
    rows = CommunityService.notes_for(book_id=request.args.get("book_id"), title=request.args.get("title"))
    return jsonify({"notes": [r.to_dict() for r in rows], "count": len(rows)})


@circle_bp.route("/notes/<uuid:note_id>", methods=["DELETE"])
@role_required(*ROLES)
def delete_note(user, note_id):
    CommunityService.delete_note(user, note_id)
    return "", 204


@circle_bp.route("/wishlist", methods=["POST"])
@role_required(*ROLES)
def wish_add(user):
    try:
        data = _load(wish_schema)
    except ValidationError as err:
        return error_response("validation_error", "Invalid input", details=err.messages, status_code=400)
    item = CommunityService.wish_add(user, data)
    return jsonify({"wish": item.to_dict()}), 201


@circle_bp.route("/wishlist/groups", methods=["GET"])
@role_required(*ROLES)
def wish_groups(user):
    return jsonify({"groups": CommunityService.wish_groups()})


@circle_bp.route("/wishlist/mine", methods=["GET"])
@role_required(*ROLES)
def wish_mine(user):
    items = CommunityService.wish_mine(user.id)
    return jsonify({"wishes": [x.to_dict() for x in items], "count": len(items)})


@circle_bp.route("/wishlist/<uuid:item_id>/close", methods=["PATCH"])
@role_required(*ROLES)
def wish_close(user, item_id):
    body = request.get_json() or {}
    item = CommunityService.wish_close(user, item_id, body.get("status", "closed"))
    return jsonify({"wish": item.to_dict()})


def _pagination_meta(pagination):
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }


@circle_bp.route("/notifications", methods=["GET"])
@role_required(*ROLES)
def list_notifications(user):
    RentalService.refresh_for_user(user)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    pagination = NotificationService.list_for(user.id, unread_only=unread_only, page=page, per_page=per_page)
    return jsonify({
        "notifications": [n.to_dict() for n in pagination.items],
        "meta": _pagination_meta(pagination),
    })


@circle_bp.route("/notifications/unread-count", methods=["GET"])
@role_required(*ROLES)
def unread_count(user):
    RentalService.refresh_for_user(user)
    return jsonify({"unread": NotificationService.unread_count(user.id)})


@circle_bp.route("/notifications/<uuid:note_id>/read", methods=["POST"])
@role_required(*ROLES)
def mark_notification_read(user, note_id):
    note = NotificationService.mark_read(user.id, note_id)
    return jsonify({"notification": note.to_dict()})


@circle_bp.route("/notifications/read-all", methods=["POST"])
@role_required(*ROLES)
def mark_all_notifications_read(user):
    count = NotificationService.mark_all_read(user.id)
    return jsonify({"marked": count})


@circle_bp.route("/rentals/mine", methods=["GET"])
@role_required(*ROLES)
def my_rentals(user):
    rentals = RentalService.my_rentals(user)
    return jsonify({"rentals": rentals, "count": len(rentals)})


@circle_bp.route("/rentals/out", methods=["GET"])
@role_required(*ROLES)
def rented_out(user):
    rentals = RentalService.rented_out(user)
    return jsonify({"rentals": rentals, "count": len(rentals)})


@circle_bp.route("/rentals/<uuid:rental_id>", methods=["GET"])
@role_required(*ROLES)
def get_rental(user, rental_id):
    rental = RentalService.get_for(user, rental_id)
    return jsonify({"rental": RentalService._serialize(rental)})


@circle_bp.route("/rentals/<uuid:rental_id>/return", methods=["POST"])
@role_required(*ROLES)
def request_rental_return(user, rental_id):
    rental = RentalService.request_return(user, rental_id)
    return jsonify({"rental": RentalService._serialize(rental)})


@circle_bp.route("/rentals/<uuid:rental_id>/return/cancel", methods=["POST"])
@role_required(*ROLES)
def cancel_rental_return(user, rental_id):
    rental = RentalService.cancel_return_request(user, rental_id)
    return jsonify({"rental": RentalService._serialize(rental)})


@circle_bp.route("/rentals/<uuid:rental_id>/return/confirm", methods=["POST"])
@role_required(*ROLES)
def confirm_rental_return(user, rental_id):
    rental = RentalService.confirm_return(user, rental_id)
    return jsonify({"rental": RentalService._serialize(rental)})


@circle_bp.route("/rentals/<uuid:rental_id>/complete", methods=["POST"])
@role_required(*ROLES)
def complete_rental_return(user, rental_id):
    data = request.get_json() or {}
    rental = RentalService.complete_return_with_details(user, rental_id, data)
    return jsonify({"rental": RentalService._serialize(rental)})


@circle_bp.route("/rentals/<uuid:rental_id>/fine", methods=["POST"])
@role_required(*ROLES)
def apply_overdue_fine(user, rental_id):
    rental = RentalService.apply_overdue_fine(user, rental_id)
    return jsonify({"rental": RentalService._serialize(rental)})
