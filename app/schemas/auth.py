import re

from marshmallow import Schema, ValidationError, fields, validates


PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$")


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    role = fields.String(required=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    phone = fields.String(load_default=None, allow_none=True)
    address = fields.String(load_default=None, allow_none=True)

    @validates("email")
    def validate_email(self, value, **kwargs):
        if len(value) > 255:
            raise ValidationError("Email must be at most 255 characters.")

    @validates("password")
    def validate_password(self, value, **kwargs):
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        if not PASSWORD_PATTERN.match(value):
            raise ValidationError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit."
            )

    @validates("role")
    def validate_role(self, value, **kwargs):
        if value not in ("seller", "buyer"):
            raise ValidationError("Role must be 'seller' or 'buyer'.")

    @validates("first_name")
    def validate_first_name(self, value, **kwargs):
        trimmed = value.strip()
        if not trimmed or len(trimmed) > 100:
            raise ValidationError("First name must be between 1 and 100 characters.")

    @validates("last_name")
    def validate_last_name(self, value, **kwargs):
        trimmed = value.strip()
        if not trimmed or len(trimmed) > 100:
            raise ValidationError("Last name must be between 1 and 100 characters.")

    @validates("phone")
    def validate_phone(self, value, **kwargs):
        if value is not None and len(value.strip()) > 50:
            raise ValidationError("Phone must be at most 50 characters.")

    @validates("address")
    def validate_address(self, value, **kwargs):
        if value is not None and len(value.strip()) > 500:
            raise ValidationError("Address must be at most 500 characters.")


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class RefreshTokenSchema(Schema):
    refresh_token = fields.String(required=True)


class LogoutSchema(Schema):
    refresh_token = fields.String(required=True)


class UserResponseSchema(Schema):
    id = fields.String()
    email = fields.Email()
    role = fields.String()
    first_name = fields.String()
    last_name = fields.String()
    phone = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    created_at = fields.String()
