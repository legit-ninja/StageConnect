import uuid

from sqlalchemy.orm import Session

from app.models.thread import Thread


def create_promoter_connection_thread(db: Session, promoter_connection_id: uuid.UUID) -> Thread:
    thread = Thread(promoter_connection_id=promoter_connection_id)
    db.add(thread)
    db.flush()
    return thread


def create_gig_thread(db: Session, gig_request_id: uuid.UUID) -> Thread:
    thread = Thread(gig_request_id=gig_request_id)
    db.add(thread)
    db.flush()
    return thread
