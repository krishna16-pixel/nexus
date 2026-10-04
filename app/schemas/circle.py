from marshmallow import Schema, ValidationError, fields, validates


class CircleListingSchema(Schema):
    book_id = fields.UUID(allow_none=True)
    title = fields.String(allow_none=True)
    author = fields.String(allow_none=True)
    offer_type = fields.String(required=True)
    price = fields.Decimal(as_string=True, allow_none=True)
    rent_fee = fields.Decimal(as_string=True, allow_none=True)
    rent_days = fields.Integer(allow_none=True)
    rent_hours = fields.Integer(allow_none=True)
    rent_mins = fields.Integer(allow_none=True)
    description = fields.String(allow_none=True)
    city = fields.String(allow_none=True)
    campus = fields.String(allow_none=True)

    @validates("offer_type")
    def validate_type(self, value, **kwargs):
        if value not in ("sell", "rent", "donate", "exchange"):
            raise ValidationError("offer_type must be one of: sell, rent, donate, exchange.")


class ClaimSchema(Schema):
    message = fields.String(allow_none=True)


class SwapSchema(Schema):
    wanted_listing_id = fields.UUID(required=True)
    offered_listing_id = fields.UUID(required=True)
    message = fields.String(allow_none=True)


class ReadingSchema(Schema):
    book_id = fields.UUID(allow_none=True)
    title = fields.String(allow_none=True)
    author = fields.String(allow_none=True)
    state = fields.String(load_default="reading")
    city = fields.String(allow_none=True)
    campus = fields.String(allow_none=True)

    @validates("state")
    def validate_state(self, value, **kwargs):
        if value not in ("reading", "finished"):
            raise ValidationError("state must be reading or finished.")


class BuddyRequestSchema(Schema):
    target_id = fields.UUID(required=True)
    message = fields.String(allow_none=True)


class DetectiveSchema(Schema):
    title = fields.String(required=True)
    author = fields.String(allow_none=True)
    max_price = fields.Decimal(as_string=True, allow_none=True)
    city = fields.String(allow_none=True)
    note = fields.String(allow_none=True)

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value.strip() or len(value.strip()) > 255:
            raise ValidationError("Title must be 1-255 characters.")


class DetectiveOfferSchema(Schema):
    book_id = fields.UUID(allow_none=True)
    price = fields.Decimal(as_string=True, allow_none=True)
    message = fields.String(allow_none=True)


class PriceSuggestSchema(Schema):
    book_id = fields.UUID(allow_none=True)
    original_price = fields.Decimal(as_string=True, allow_none=True)
    condition = fields.String(required=True)
    age_years = fields.Integer(load_default=0)
    edition = fields.String(allow_none=True)


class NoteSchema(Schema):
    book_id = fields.UUID(allow_none=True)
    title = fields.String(allow_none=True)
    author = fields.String(allow_none=True)
    note = fields.String(required=True)

    @validates("note")
    def validate_note(self, value, **kwargs):
        if not value.strip() or len(value.strip()) > 2000:
            raise ValidationError("Note must be 1-2000 characters.")


class InterestSchema(Schema):
    genres = fields.String(allow_none=True)
    favorite_authors = fields.String(allow_none=True)
    note = fields.String(allow_none=True)


class WishSchema(Schema):
    book_id = fields.UUID(allow_none=True)
    title = fields.String(allow_none=True)
    author = fields.String(allow_none=True)
    city = fields.String(allow_none=True)
    campus = fields.String(allow_none=True)
    max_price = fields.Decimal(as_string=True, allow_none=True)
