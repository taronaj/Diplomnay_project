from fastapi import APIRouter, Depends, status

from pkg.controllers.middlewares import get_current_user
from pkg.services import course_service
from pkg.services import event as event_service
from schemas.course_schemas import CourseListResponse, CourseSchema, MessageResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get(
    "/",
    summary="Получить список курсов",
    response_model=CourseListResponse,
)
def get_courses():
    return {"courses": course_service.get_courses()}


@router.post(
    "/",
    summary="Создать новый курс",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(course_schema: CourseSchema, payload=Depends(get_current_user)):
    result = course_service.create_course(payload.id, course_schema)
    event_service.log_event(
        user_id=payload.id,
        event_type="course_create",
        event_description=f"Пользователь {payload.id} создал курс '{course_schema.name}'",
    )
    return result


@router.put(
    "/{course_id}",
    summary="Обновить курс по ID",
    response_model=MessageResponse,
)
def update_course(course_id: int, course_schema: CourseSchema, payload=Depends(get_current_user)):
    result = course_service.update_course(payload.id, course_schema, course_id)
    event_service.log_event(
        user_id=payload.id,
        event_type="course_update",
        event_description=f"Пользователь {payload.id} обновил курс #{course_id} ('{course_schema.name}')",
        related_id=course_id,
    )
    return result


@router.delete(
    "/{course_id}",
    summary="Удалить курс по ID",
    response_model=MessageResponse,
)
def delete_course(course_id: int, payload=Depends(get_current_user)):
    result = course_service.delete_course(payload.id, course_id)
    event_service.log_event(
        user_id=payload.id,
        event_type="course_delete",
        event_description=f"Пользователь {payload.id} удалил курс #{course_id}",
        related_id=course_id,
    )
    return result
