import json

from fastapi import APIRouter, status, Depends

from starlette.responses import Response, JSONResponse

from pkg.controllers.middlewares import get_current_user
from utils.auth import TokenPayload
from db.models import Attendance
from pkg.services import attendances as attendances_service
from pkg.services import event as event_service
from schemas.attendance import AttendanceSchema

router = APIRouter()


@router.get("/course/attendances/{course_id}", summary="get all attendances", tags=["attendances"])
def get_all_attendances(course_id: int, response: Response):
    attendances = attendances_service.get_all_attendances(course_id)
    response.status_code = status.HTTP_200_OK
    response.headers["Content-Type"] = "application/json"
    return attendances


@router.get("/attendances/{attendance_id}", summary="get attendance by id", tags=["attendances"])
def get_attendance_by_id(attendance_id: int, response: Response):
    attendance = attendances_service.get_attendance_by_id(attendance_id)
    response.status_code = status.HTTP_200_OK
    response.headers["Content-Type"] = "application/json"
    return attendance


@router.post("/attendances", summary="create attendance", tags=["attendances"])
def create_attendance(attendance: AttendanceSchema, payload: TokenPayload = Depends(get_current_user)):
    user_id = payload.id
    response = attendances_service.create_attendance(user_id, attendance)
    if not response[1]:
        return JSONResponse(response[0], status_code=status.HTTP_400_BAD_REQUEST)
    event_service.log_event(
        user_id=user_id,
        event_type="attendance_create",
        event_description=f"Пользователь {user_id} создал посещаемость для студента #{attendance.user_id} на уроке #{attendance.lesson_id}",
        related_id=attendance.lesson_id,
    )
    return JSONResponse({"message": "Attendance created"}, status_code=status.HTTP_201_CREATED)


@router.put("/attendances/{attendance_id}", summary="update attendance by id", tags=["attendances"])
def update_attendance(attendance_id: int, attendance: AttendanceSchema, payload: TokenPayload = Depends(get_current_user)):
    user_id = payload.id
    response = attendances_service.update_attendance(user_id, attendance_id, attendance)
    if response is not None:
        return JSONResponse(response, status_code=status.HTTP_400_BAD_REQUEST)
    event_service.log_event(
        user_id=user_id,
        event_type="attendance_update",
        event_description=f"Пользователь {user_id} обновил посещаемость #{attendance_id}",
        related_id=attendance_id,
    )
    return JSONResponse({"message": "attendance updated"}, status_code=status.HTTP_200_OK)


@router.delete("/attendances/{attendance_id}", summary="delete attendance by id", tags=["attendances"])
def delete_attendance_by_id(attendance_id: int, payload: TokenPayload = Depends(get_current_user)):
    user_id = payload.id
    attendances_service.delete_attendance(user_id, attendance_id)
    event_service.log_event(
        user_id=user_id,
        event_type="attendance_delete",
        event_description=f"Пользователь {user_id} удалил посещаемость #{attendance_id}",
        related_id=attendance_id,
    )
    return JSONResponse({"message": "attendance deleted"})

