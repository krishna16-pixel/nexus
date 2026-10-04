import uuid

from app.extensions import db
from app.models import Notification
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
