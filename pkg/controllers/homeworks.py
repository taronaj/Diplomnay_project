from fastapi import APIRouter, HTTPException, status, Depends
from starlette.responses import Response
import json

from pkg.controllers.middlewares import get_current_user, require_roles
from pkg.services import homework_service as homework_service
from pkg.services import event as event_service
from schemas.homeworks import HomeworkSchema, HomeworkUpdateSchema
from logger.logger import logger

router = APIRouter()



from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from typing import Union


@router.get("/homeworks/{homework_id}", summary="Get student homework", tags=["homeworks"])
def get_homework(homework_id: int, payload=Depends(get_current_user)):
    user_id = payload.id
    logger.info(f"Запрос домашнего задания {homework_id} для пользователя {user_id}")

    homework = homework_service.get_student_homeworks(user_id, homework_id)

    if not homework:
        return JSONResponse(
            content={"error": "Homework not found"},
            status_code=status.HTTP_404_NOT_FOUND
        )

    return JSONResponse(content={"homework": homework}, status_code=status.HTTP_200_OK)


@router.post("/homeworks", summary="Add homework", tags=["homeworks"])
def add_homework(homework: HomeworkSchema, payload=Depends(require_roles("Администратор", "Преподаватель"))):
    user_id = payload.id
    logger.info(
        f"Пользователь {user_id} добавляет домашнее задание для студента {homework.student_id} "
        f"на урок {homework.lesson_id} с оценкой {homework.score} для курса {homework.course_id} "
        f"с содержимым: {homework.homework}"
    )
    # Передаем user_id (int) и объект схемы homework
    homework_id = homework_service.add_homework(user_id, homework)
    event_service.log_event(
        user_id=user_id,
        event_type="homework_add",
        event_description=f"Ментор {user_id} добавил домашнее задание студенту #{homework.student_id} для урока #{homework.lesson_id}",
        related_id=homework_id,
    )
    logger.info(f"Домашнее задание успешно добавлено пользователем {user_id}")
    return Response(
        json.dumps({'message': 'Homework successfully added', 'homework_id': homework_id}),
        status_code=status.HTTP_201_CREATED,
        media_type="application/json"
    )


@router.put("/homeworks/{homework_id}", summary="Edit homework", tags=["homeworks"])
def edit_homework(homework_id: int, homework_data: HomeworkUpdateSchema, payload=Depends(require_roles("Администратор", "Преподаватель"))):
    user_id = payload.id
    logger.info(
        f"Пользователь {user_id} редактирует домашнее задание {homework_id} с новой оценкой {homework_data.score}"
    )
    updated_homework = homework_service.edit_homework(user_id, homework_id, homework_data.score)
    if not updated_homework:
        logger.error(f"Пользователь {user_id} не нашёл домашнее задание {homework_id} для обновления")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")
    event_service.log_event(
        user_id=user_id,
        event_type="homework_update",
        event_description=f"Ментор {user_id} обновил домашнее задание #{homework_id}",
        related_id=homework_id,
    )
    logger.info(f"Домашнее задание {homework_id} успешно обновлено пользователем {user_id}")
    return Response(
        json.dumps({"message": "Homework updated successfully", "homework": updated_homework}),
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )


@router.delete("/homeworks/{homework_id}/hard", summary="Delete homework", tags=["homeworks"])
def remove_homework(homework_id: int, payload=Depends(require_roles("Администратор", "Преподаватель"))):
    user_id = payload.id
    logger.info(f"Пользователь {user_id} пытается удалить домашнее задание {homework_id}")
    success = homework_service.remove_homework(user_id, homework_id)
    if not success:
        logger.error(f"Пользователь {user_id} не нашёл домашнее задание {homework_id} для удаления")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")
    event_service.log_event(
        user_id=user_id,
        event_type="homework_delete",
        event_description=f"Ментор {user_id} удалил домашнее задание #{homework_id}",
        related_id=homework_id,
    )
    logger.info(f"Домашнее задание {homework_id} успешно удалено пользователем {user_id}")
    return Response(
        json.dumps({'message': 'Homework successfully deleted'}),
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )


@router.delete("/homeworks/{homework_id}/soft", summary="Soft delete homework", tags=["homeworks"])
def soft_delete_homework(homework_id: int, payload=Depends(require_roles("Администратор", "Преподаватель"))):
    user_id = payload.id
    logger.info(f"Пользователь {user_id} пытается выполнить soft delete домашнего задания {homework_id}")
    success = homework_service.soft_delete_homework(user_id, homework_id)
    if not success:
        logger.error(f"Пользователь {user_id} не нашёл домашнее задание {homework_id} для soft delete")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")
    event_service.log_event(
        user_id=user_id,
        event_type="homework_soft_delete",
        event_description=f"Ментор {user_id} выполнил soft delete домашнего задания #{homework_id}",
        related_id=homework_id,
    )
    logger.info(f"Домашнее задание {homework_id} успешно помечено как удалённое (soft deleted) пользователем {user_id}")
    return Response(
        json.dumps({'message': 'Homework successfully soft deleted'}),
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )
