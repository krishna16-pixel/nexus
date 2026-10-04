"""Create temporary demo buyer and seller accounts for local testing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User, UserRole

DEMO_PASSWORD = "Demo@12345"
DEMO_USERS = [
    {
        "email": "demo.buyer@example.com",
        "role": UserRole.buyer,
        "first_name": "Demo",
        "last_name": "Buyer",
        "phone": "+91 90000 00001",
        "address": "Demo Buyer, 12 Reader Lane, Bengaluru, Karnataka",
    },
    {
        "email": "demo.seller@example.com",
        "role": UserRole.seller,
        "first_name": "Demo",
        "last_name": "Seller",
        "phone": "+91 90000 00002",
        "address": "Demo Seller, 45 Book Street, Bengaluru, Karnataka",
    },
]


def seed() -> None:
    app = create_app()
    with app.app_context():
        for data in DEMO_USERS:
            user = User.query.filter_by(email=data["email"]).first()
            if user is None:
                user = User(email=data["email"])
                db.session.add(user)
            user.role = data["role"]
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            user.phone = data["phone"]
            user.address = data["address"]
            user.is_active = True
            user.set_password(DEMO_PASSWORD)
        db.session.commit()
        print("Demo accounts ready:")
        print("  Buyer:  demo.buyer@example.com")
        print("  Seller: demo.seller@example.com")
        print(f"  Password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
