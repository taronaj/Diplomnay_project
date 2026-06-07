from db.models import Event
from pkg.repositories import event as event_repository
from schemas.event import EventSchema


def get_recent_events():
    return event_repository.get_recent_events()


def create_event(event: EventSchema):
    e = Event()
    e.user_id = event.user_id
    e.event_type = event.event_type
    e.event_description = event.event_description
    e.related_id = event.related_id

    return event_repository.create_event(e)


def update_event(event_id: int, event: EventSchema):
    service_event = event_repository.get_event_by_id(event_id)
    if not service_event:
        return None

    service_event.user_id = event.user_id
    service_event.event_type = event.event_type
    service_event.event_description = event.event_description
    service_event.related_id = event.related_id

    return event_repository.update_event(event_id, service_event)


def soft_delete_event(event_id: int):
    return event_repository.soft_delete_event(event_id)


def hard_delete_event(event_id: int):
    return event_repository.hard_delete_event(event_id)


def log_event(user_id: int, event_type: str, event_description: str, related_id: int | None = None):
    e = Event()
    e.user_id = user_id
    e.event_type = event_type
    e.event_description = event_description
    e.related_id = related_id
    return event_repository.create_event(e)
