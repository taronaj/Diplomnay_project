from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError

from logger.logger import logger
from pkg.controllers.middlewares import get_current_user, require_roles
from pkg.services import event as event_service
from pkg.services import lesson_material as material_service

MAX_ALLOWED_SIZE = 1048576 * 5
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".png", ".jpg", ".jpeg"}

router = APIRouter(tags=["Lesson materials"])


@router.post("/lesson-materials/{lesson_id}", summary="Upload a lesson material")
def upload_file(
    lesson_id: int,
    file: UploadFile = File(...),
    payload=Depends(require_roles("Администратор", "Преподаватель")),
):
    if file.size and file.size > MAX_ALLOWED_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size must be <= 5 MB")

    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    if material_service.get_material_by_filename(file.filename) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"File {file.filename} already exists")

    try:
        material_service.upload_file(lesson_id, file)
    except SQLAlchemyError as exc:
        logger.exception("Material upload database error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from exc

    event_service.log_event(
        user_id=payload.id,
        event_type="material_upload",
        event_description=f"Пользователь {payload.id} загрузил материал '{file.filename}' для урока #{lesson_id}",
        related_id=lesson_id,
    )
    return {"message": "File uploaded successfully"}


@router.get("/lesson-materials/{lesson_id}", summary="Get lesson materials")
def get_all_materials(lesson_id: int, payload=Depends(get_current_user)):
    return material_service.get_all_materials(lesson_id)


@router.get("/lesson-materials/file/{file_id}", summary="Download lesson material")
def get_material_by_id(file_id: int, payload=Depends(get_current_user)):
    file_to_download = material_service.get_material_by_id(file_id)
    if file_to_download is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file_path, filename = file_to_download
    if not Path(file_path).exists():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="File does not exist on server")
    return FileResponse(file_path, filename=filename)


@router.put("/lesson-materials/file/{file_id}", summary="Update lesson material")
def update_file(
    file_id: int,
    file: UploadFile = File(...),
    payload=Depends(require_roles("Администратор", "Преподаватель")),
):
    if file.size and file.size > MAX_ALLOWED_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size must be <= 5 MB")
    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    new_file_path = material_service.update_file(file_id, file)
    if new_file_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    event_service.log_event(
        user_id=payload.id,
        event_type="material_update",
        event_description=f"Пользователь {payload.id} обновил материал #{file_id} на файл '{file.filename}'",
        related_id=file_id,
    )
    return {"message": "File updated successfully"}


@router.delete("/lesson-materials/file/{file_id}", summary="Delete lesson material")
def delete_file(file_id: int, payload=Depends(require_roles("Администратор", "Преподаватель"))):
    if material_service.delete_file(file_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    event_service.log_event(
        user_id=payload.id,
        event_type="material_delete",
        event_description=f"Пользователь {payload.id} удалил материал #{file_id}",
        related_id=file_id,
    )
    return {"message": "File deleted successfully"}
