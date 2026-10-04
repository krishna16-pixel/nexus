import uuid
from decimal import Decimal

from app.extensions import db
from app.models import Notification, Order, OrderItem, OrderStatus, User
from app.utils.exceptions import ForbiddenError, NotFoundError


class NotificationService:
    @staticmethod
    def notify(user_id: uuid.UUID, kind: str, title: str, message: str | None = None,
               link: str | None = None, ref_type: str | None = None, ref_id=None) -> Notification:
        note = Notification(
            user_id=user_id,
            kind=kind,
            title=title[:255],
            message=message,
            link=link,
            ref_type=ref_type,
            ref_id=str(ref_id) if ref_id is not None else None,
        )
        db.session.add(note)
        return note

    @staticmethod
    def list_for(user_id: uuid.UUID, page: int = 1, per_page: int = 20, unread_only: bool = False):
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def unread_count(user_id: uuid.UUID) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def mark_read(user_id: uuid.UUID, note_id: uuid.UUID) -> Notification:
        note = db.session.get(Notification, note_id)
        if note is None or note.user_id != user_id:
            raise NotFoundError("Notification not found")
        note.is_read = True
        db.session.commit()
        return note

    @staticmethod
    def mark_all_read(user_id: uuid.UUID) -> int:
        notes = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for note in notes:
            note.is_read = True
        db.session.commit()
        return len(notes)


def _person(user: User | None) -> str:
    if user is None:
        return "Unknown"
    return f"{user.first_name} {user.last_name}".strip() or user.email


def _money(value) -> str:
    return f"{Decimal(str(value or 0)):.2f}"


def _address(order: Order) -> str:
    parts = [
        order.shipping_line1,
        order.shipping_line2,
        order.shipping_city,
        order.shipping_state,
        order.shipping_postal_code,
        order.shipping_country,
    ]
    return ", ".join(p for p in parts if p) or "not provided"


def _books_text(items) -> str:
    return "\n".join(
        f"• {item.title} by {item.author} × {item.quantity} = ₹{_money(item.unit_price * item.quantity)}"
        for item in items
    )


class OrderNotifications:
    """WhatsApp-style order updates for sellers and buyers (cash-on-delivery orders)."""

    @staticmethod
    def placed(order: Order, buyer: User, seller: User, items: list[OrderItem]) -> None:
        total = _money(order.subtotal)
        ref = {"link": f"/orders/{order.id}", "ref_type": "order", "ref_id": order.id}
        NotificationService.notify(
            seller.id, "order_placed",
            f"New order from {_person(buyer)}",
            "\n".join([
                f"Buyer: {_person(buyer)}",
                f"Phone: {buyer.phone or 'not provided'}",
                f"Email: {buyer.email}",
                f"Delivery address: {_address(order)}",
                "Books:",
                _books_text(items),
                f"Order total: ₹{total}",
                f"Payment: cash on delivery. Collect ₹{total} when you hand over the books.",
            ]),
            **ref,
        )
        NotificationService.notify(
            buyer.id, "order_placed_buyer",
            f"Order placed with {_person(seller)}",
            "\n".join([
                "Books:",
                _books_text(items),
                f"Total: ₹{total}",
                f"Payment: cash on delivery. Pay ₹{total} to the courier when the books are delivered.",
                f"Delivering to: {_address(order)}",
                f"Seller: {_person(seller)} · phone {seller.phone or 'not provided'}",
                f"Seller address: {seller.address or 'not provided'}",
                "Status: placed. You will be notified when the seller confirms, ships and delivers.",
            ]),
            **ref,
        )

    @staticmethod
    def status_changed(order: Order, new_status: OrderStatus, courier_name: str | None = None) -> None:
        """Notify the buyer when the seller moves an order forward or cancels it."""
        total = _money(order.subtotal)
        seller = order.seller
        buyer = order.buyer
        ref = {"link": f"/orders/{order.id}", "ref_type": "order", "ref_id": order.id}

        if new_status == OrderStatus.confirmed:
            NotificationService.notify(
                buyer.id, "order_confirmed",
                f"Order confirmed by {_person(seller)}",
                "\n".join([
                    "Books:",
                    _books_text(order.items),
                    f"Pay ₹{total} in cash when the books are delivered.",
                    f"Delivering to: {_address(order)}",
                ]),
                **ref,
            )
        elif new_status == OrderStatus.shipped:
            NotificationService.notify(
                buyer.id, "order_shipped",
                "Your order has been shipped",
                "\n".join([
                    f"Courier: {courier_name or 'not specified'}",
                    "Books:",
                    _books_text(order.items),
                    f"Delivering to: {_address(order)}",
                    f"Pay ₹{total} in cash to the courier when the books are delivered.",
                ]),
                **ref,
            )
        elif new_status == OrderStatus.delivered:
            NotificationService.notify(
                buyer.id, "order_delivered",
                "Your order has been delivered",
                "\n".join([
                    "Books:",
                    _books_text(order.items),
                    f"Amount paid on delivery (cash on delivery): ₹{total}",
                    "Thank you. You can rate the seller and courier in My Orders.",
                ]),
                **ref,
            )
        elif new_status == OrderStatus.cancelled:
            NotificationService.notify(
                buyer.id, "order_cancelled",
                f"Order cancelled by {_person(seller)}",
                "\n".join([
                    "Books:",
                    _books_text(order.items),
                    "The seller cancelled this order. You have nothing to pay.",
                ]),
                **ref,
            )

    @staticmethod
    def buyer_cancelled(order: Order) -> None:
        """Notify the seller that the buyer cancelled a placed order."""
        buyer = order.buyer
        NotificationService.notify(
            order.seller_id, "order_cancelled_by_buyer",
            f"Order cancelled by {_person(buyer)}",
            "\n".join([
                f"Buyer: {_person(buyer)}",
                f"Phone: {buyer.phone or 'not provided'}",
                f"Delivery address: {_address(order)}",
                "Books:",
                _books_text(order.items),
                f"Order total: ₹{_money(order.subtotal)}. Stock has been restored.",
            ]),
            link=f"/orders/{order.id}", ref_type="order", ref_id=order.id,
        )
