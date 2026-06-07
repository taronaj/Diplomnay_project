import json
from fastapi import APIRouter, status, HTTPException, Depends
from starlette.responses import Response

from pkg.controllers.middlewares import get_current_user, require_roles
from pkg.services import event as event_service
from schemas.event import EventSchema


router = APIRouter()


@router.get("/events", summary="Get recent events", tags=["events"])
def get_recent_events():
    events = event_service.get_recent_events()
    return events


@router.post("/events", summary="Create a new event", tags=["events"])
def create_event(event: EventSchema, payload=Depends(require_roles("Администратор"))):
    event_id = event_service.create_event(event)
    return Response(json.dumps({'message': 'Event successfully created', 'event_id': event_id}),
                    status_code=status.HTTP_201_CREATED,
                    media_type='application/json')


@router.put("/events/{event_id}")
def update_event(event_id: int, event: EventSchema, payload=Depends(require_roles("Администратор"))):
    updated_event = event_service.update_event(event_id, event)

    if not updated_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    return {"message": "Event updated successfully", "event": updated_event}


@router.delete("/events/{event_id}", summary="Soft delete an event", tags=["events"])
def soft_delete_event(event_id: int, payload=Depends(require_roles("Администратор"))):
    event = event_service.soft_delete_event(event_id)
    if event is None:
        return Response(
            json.dumps({'error': 'Event not found'}),
            status_code=status.HTTP_404_NOT_FOUND
        )

    return Response(
        json.dumps({'message': 'Event successfully soft deleted'}),
        status_code=status.HTTP_200_OK
    )


@router.delete("/events/{event_id}/hard", summary="Hard delete an event", tags=["events"])
def hard_delete_event(event_id: int, payload=Depends(require_roles("Администратор"))):
    event = event_service.hard_delete_event(event_id)
    if event is None:
        return Response(
            json.dumps({'error': 'Event not found'}),
            status_code=status.HTTP_404_NOT_FOUND
        )

    return Response(
        json.dumps({'message': 'Event successfully hard deleted'}),
        status_code=status.HTTP_200_OK
    )
