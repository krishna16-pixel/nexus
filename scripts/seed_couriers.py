"""Seed courier partners. Run: python scripts/seed_couriers.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import CourierPartner

COURIERS = [
    {"name": "FastTrack Delivery", "phone": "+91-9876543210"},
    {"name": "BlueDart Express", "phone": "+91-9876543211"},
    {"name": "CityCourier", "phone": "+91-9876543212"},
    {"name": "QuickShip Logistics", "phone": "+91-9876543213"},
    {"name": "NationWide Parcel", "phone": "+91-9876543214"},
]


def seed():
    app = create_app()
    with app.app_context():
        existing = CourierPartner.query.count()
        if existing > 0:
            print(f"Skipping seed: {existing} couriers already exist.")
            return
        for data in COURIERS:
            db.session.add(CourierPartner(**data))
        db.session.commit()
        print(f"Seeded {len(COURIERS)} courier partners.")


if __name__ == "__main__":
    seed()
