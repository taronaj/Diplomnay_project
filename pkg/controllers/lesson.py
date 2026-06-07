
from fastapi import APIRouter, HTTPException, status, Depends
from starlette.responses import Response, JSONResponse
from pkg.controllers.middlewares import get_current_user
from pkg.services import lesson as lesson_service
from pkg.services import event as event_service
from schemas.lesson import LessonSchema
from logger.logger import logger

from utils.auth import TokenPayload

router = APIRouter()


# просмотр уроков, уровень доступа ментор, студент зависимость подписка на курс
@router.get("/lesson/{course_id}", summary="Get all lessons", tags=["lessons"])
def get_all_lessons(course_id: int, payload: TokenPayload = Depends(get_current_user)):
    if not lesson_service.is_admin_or_mentor(payload.id) and not lesson_service.is_user_has_access_to_lesson(payload.id, course_id):
        logger.error(f"Пользователь {payload.id} не имеет доступа к курсу {course_id} и его урокам")
        raise HTTPException(
            status_code=403, detail="Пользователь не имеет доступа к этому курсу и его урокам.")

    logger.info(f"Пользователь {payload.id} получил уроки курса {course_id}")

    return lesson_service.get_lesson(course_id)


# просмотр урока, уровень доступа ментор, студент зависимость подписка на курс
@router.get("/lesson/{course_id}/{lesson_id}", summary="Get lessons by ID", tags=["lessons"])
def get_lesson_by_id(course_id: int, lesson_id: int, payload: TokenPayload = Depends(get_current_user)):
    if not lesson_service.is_admin_or_mentor(payload.id) and not lesson_service.is_user_has_access_to_lesson(payload.id, course_id):
        logger.error(f"Пользователь {payload.id} не имеет доступа к курсу {course_id} и его урокам")
        raise HTTPException(
            status_code=403, detail="Пользователь не имеет доступа к этому курсу и его урокам.")

    lesson = lesson_service.get_lesson_by_id(course_id, lesson_id)
    if lesson is None:
        return JSONResponse({"message": "Урок не найден"}, status_code=status.HTTP_404_NOT_FOUND)
    
    logger.info(f"Пользователь {payload.id} получил урок {lesson_id} курса {course_id}")
    
    return lesson


# добавление урока, уровень доступа ментор зависимость подписка на курс
@router.post("/lesson/{course_id}", summary="Greate new lesson", tags=["lessons"])
def create_lesson(course_id: int, lesson: LessonSchema, payload: TokenPayload = Depends(get_current_user)):
    if not lesson_service.is_admin_or_mentor(payload.id):
        logger.error(f"Пользователь {payload.id} не имеет прав для создания урока")
        raise HTTPException(
            status_code=403, detail="Пользователь не имеет прав для создания урока")

    if not lesson_service.is_course_exists(course_id):
        return JSONResponse({"message": "Курс не найден"}, status_code=status.HTTP_404_NOT_FOUND)

    lesson_service.create_lesson(course_id, lesson)
    event_service.log_event(
        user_id=payload.id,
        event_type="lesson_create",
        event_description=f"Пользователь {payload.id} создал урок '{lesson.title}' в курсе #{course_id}",
        related_id=course_id,
    )
    
    logger.info(f"Пользователь {payload.id} успешно создал урок для курса {course_id}")
    
    return JSONResponse({"message": "Урок успешно создан"}, status_code=status.HTTP_201_CREATED)


# изменение урока, уровень доступа ментор зависимость подписка на курс
@router.put("/lesson/{course_id}/{lesson_id}", summary="Update lesson", tags=["lessons"])
def update_lesson(course_id: int, lesson_id: int, lesson: LessonSchema, payload: TokenPayload = Depends(get_current_user)):
    if not lesson_service.is_admin_or_mentor(payload.id):
        logger.error(f"Пользователь {payload.id} не имеет прав для обновления урока {lesson_id}")
        raise HTTPException(
            status_code=403, detail="Пользователь не имеет прав для обновления урока")

    if not lesson_service.is_course_exists(course_id):
        return JSONResponse({"message": "Курс не найден"}, status_code=status.HTTP_404_NOT_FOUND)

    lesson = lesson_service.update_lesson(course_id, lesson_id, lesson)
    if lesson is None:
        return JSONResponse({"message": "Урок не найден"}, status_code=status.HTTP_404_NOT_FOUND)
    event_service.log_event(
        user_id=payload.id,
        event_type="lesson_update",
        event_description=f"Пользователь {payload.id} обновил урок #{lesson_id} в курсе #{course_id}",
        related_id=lesson_id,
    )
    
    logger.info(f"Пользователь {payload.id} успешно обновил урок {lesson_id}")

    return JSONResponse({"message": "Урок успешно обновлен"}, status_code=status.HTTP_200_OK)


# удаление урока, уровень доступа ментор зависимость подписка на курс
@router.delete("/lesson/{course_id}/{lesson_id}", summary="Delete lesson", tags=["lessons"])
def delete_lesson(course_id: int, lesson_id: int, payload: TokenPayload = Depends(get_current_user)):
    if not lesson_service.is_admin_or_mentor(payload.id):
        logger.error(f"Пользователь {payload.id} не имеет прав для удаления урока {lesson_id}")
        raise HTTPException(
            status_code=403, detail="Пользователь не имеет прав для удаления урока")

    lesson = lesson_service.delete_lesson(course_id, lesson_id)
    logger.info(f"Урок {lesson_id} успешно удален")
    if lesson is None:
        return JSONResponse({"message": "Урок не найден"}, status_code=status.HTTP_404_NOT_FOUND)

    event_service.log_event(
        user_id=payload.id,
        event_type="lesson_delete",
        event_description=f"Пользователь {payload.id} удалил урок #{lesson_id} из курса #{course_id}",
        related_id=lesson_id,
    )

    logger.info(f"Пользователь {payload.id} успешно удалил урок {lesson_id}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
