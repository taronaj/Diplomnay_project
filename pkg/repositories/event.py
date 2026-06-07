import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.postgres import engine
from db.models import Event


def create_event(event: Event):
    with Session(bind=engine) as db:
        event_db = Event(
            user_id=event.user_id,
            event_type=event.event_type,
            event_description=event.event_description,
            related_id=event.related_id,
        )
        db.add(event_db)
        db.commit()
        db.refresh(event_db)
        return event_db.id


def get_recent_events():
    with Session(bind=engine) as db:
        return db.query(Event).filter(Event.deleted_at == None).order_by(desc(Event.created_at)).all()


def get_event_by_id(event_id: int):
    with Session(bind=engine) as db:
        return db.query(Event).filter(Event.id == event_id, Event.deleted_at == None).first()


def update_event(event_id: int, event: Event):
    with Session(bind=engine) as db:
        db_event = db.query(Event).filter(Event.id == event_id, Event.deleted_at == None).first()
        if not db_event:
            return None

        db_event.user_id = event.user_id
        db_event.event_type = event.event_type
        db_event.event_description = event.event_description
        db_event.related_id = event.related_id
        db_event.updated_at = datetime.datetime.now()

        db.commit()

    return db_event


def soft_delete_event(event_id: int):
    with Session(bind=engine) as db:
        event = db.query(Event).filter(Event.id == event_id, Event.deleted_at == None).first()
        if not event:
            return None

        event.deleted_at = datetime.datetime.now()
        db.commit()
        return event


def hard_delete_event(event_id: int):
    with Session(bind=engine) as db:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return None

        db.delete(event)
        db.commit()
        return event
