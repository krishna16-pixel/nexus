# BookVerse — Book Store Marketplace

A full-stack book marketplace with a **landing page**, separate **seller** and **buyer** portals, JWT auth, catalog management, cart/checkout (Cash on Delivery), and post-delivery ratings.

## Stack

- **Backend:** Python Flask, SQLite, SQLAlchemy, JWT
- **Frontends:** React + TypeScript + Vite
  - Landing: `http://localhost:5172`
  - Seller portal: `http://localhost:5173`
  - Buyer portal: `http://localhost:5174`

## Local Quick Start

No Docker or PostgreSQL is required. The cleaned project uses SQLite and creates the database in `instance/bookstore.db`.

### 1. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app run:app db upgrade
python scripts/seed_couriers.py
python scripts/seed_demo_users.py
python run.py
```

API: `http://127.0.0.1:5000`

### Demo login accounts

These temporary accounts are included for local testing:

| Role | Email | Password |
|------|-------|----------|
| Buyer | `demo.buyer@example.com` | `Demo@12345` |
| Seller | `demo.seller@example.com` | `Demo@12345` |

Run `python scripts/seed_demo_users.py` again to recreate or reset these demo accounts.

### Rental handover and return details

- New registrations can optionally save a **phone number** and **handover address**.
- Both renter and owner receive notifications showing the book name, participant name, due time, rent, fine, and total amount due.
- Reminders are generated at **1 day** and **1 hour** before the due time.
- After a full overdue day, both users receive a follow-up explaining that the owner may contact the renter to arrange collection; the owner sees the renter’s saved phone and address.
- The return flow shows the due time, return time, participant details, fine, expected amount, amount paid/collected, payment method, and notes.

### 2. Frontends

Open the **landing page** first — it links to both portals:

```bash
# Landing (start here; run each app in its own terminal)
cd frontend/landing && npm install && npm run dev

# Seller portal
cd frontend/seller-portal && npm install && npm run dev

# Buyer portal
cd /path/to/book-store-master/frontend/buyer-portal && npm install && npm run dev
```

| App | URL | Purpose |
|-----|-----|---------|
| Landing | http://localhost:5172 | Choose seller or buyer portal |
| Seller | http://localhost:5173 | Manage books & orders |
| Buyer | http://localhost:5174 | Shop, cart, COD checkout, ratings |

## User Flow

1. Visit **landing** → click Seller or Buyer portal card
2. **Seller:** Register → add books → fulfill orders (confirm → ship → deliver)
3. **Buyer:** Register → browse → cart → COD checkout → rate seller & courier when delivered

## Design

Shared design system in `frontend/shared/styles/theme.css`:

- **Fraunces** display + **DM Sans** body typography
- Seller theme: teal accents
- Buyer theme: purple accents
- Sidebar navigation, split auth layouts, polished tables and cards

## API Overview

| Prefix | Role |
|--------|------|
| `/api/v1/auth` | Register, login, tokens |
| `/api/v1/seller` | Books, orders, couriers |
| `/api/v1/buyer` | Catalog, cart, checkout, ratings |

## Environment

See `.env.example` for SQLite, `CORS_ORIGINS`, and portal URLs. Do not commit or copy `node_modules` or `dist` directories.
