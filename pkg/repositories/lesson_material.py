import datetime
import shutil
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import LessonMaterial
from db.postgres import engine
from logger.logger import logger

MATERIAL_STORAGE = Path.cwd() / "lesson_materials"


def save_file(lesson_id: int, file) -> None:
    subfolder = MATERIAL_STORAGE / str(lesson_id)
    subfolder.mkdir(parents=True, exist_ok=True)
    file_path = subfolder / file.hashed_filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


def upload_file(lesson_material: LessonMaterial) -> int:
    with Session(bind=engine) as db:
        try:
            db.add(lesson_material)
            db.commit()
            db.refresh(lesson_material)
            return lesson_material.id
        except SQLAlchemyError:
            db.rollback()
            raise


def get_all_materials(lesson_id: int) -> list[LessonMaterial]:
    with Session(bind=engine) as db:
        return (
            db.query(LessonMaterial)
            .filter(LessonMaterial.deleted_at.is_(None), LessonMaterial.lesson_id == lesson_id)
            .all()
        )


def get_material_by_filename(filename: str) -> LessonMaterial | None:
    with Session(bind=engine) as db:
        return (
            db.query(LessonMaterial)
            .filter(LessonMaterial.deleted_at.is_(None), LessonMaterial.filename == filename)
            .first()
        )


def get_material_by_id(file_id: int) -> tuple[str, str] | None:
    with Session(bind=engine) as db:
        db_material = (
            db.query(LessonMaterial)
            .filter(LessonMaterial.deleted_at.is_(None), LessonMaterial.id == file_id)
            .first()
        )
        if db_material is None:
            logger.warning("Material not found: id=%s", file_id)
            return None
        file_path = MATERIAL_STORAGE / str(db_material.lesson_id) / db_material.hashed_filename
        return str(file_path), db_material.filename


def replace_file(file_path: str | Path, file) -> Path | None:
    path = Path(file_path)
    if not path.exists():
        return None
    path.unlink()
    new_file_path = path.parent / file.hashed_filename
    with new_file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return new_file_path


def update_file(file_id: int, lesson_material: LessonMaterial) -> int | None:
    with Session(bind=engine) as db:
        try:
            db_material = (
                db.query(LessonMaterial)
                .filter(LessonMaterial.deleted_at.is_(None), LessonMaterial.id == file_id)
                .first()
            )
            if db_material is None:
                return None
            db_material.filename = lesson_material.filename
            db_material.hashed_filename = lesson_material.hashed_filename
            db_material.file_size_bytes = lesson_material.file_size_bytes
            db_material.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(db_material)
            return db_material.id
        except SQLAlchemyError:
            db.rollback()
            raise


def delete_file(file_id: int) -> int | None:
    with Session(bind=engine) as db:
        try:
            db_material = (
                db.query(LessonMaterial)
                .filter(LessonMaterial.deleted_at.is_(None), LessonMaterial.id == file_id)
                .first()
            )
            if db_material is None:
                return None
            db_material.deleted_at = datetime.datetime.now()
            db.commit()
            db.refresh(db_material)
            return db_material.id
        except SQLAlchemyError:
            db.rollback()
            raise
