from pathlib import Path

from db.models import LessonMaterial
from utils.hash import hash_filename
from pkg.repositories import lesson_material as material_repository

from logger.logger import logger


def save_file(lesson_id, file):
    hashed_filename = hash_filename(file.filename)
    file.hashed_filename = hashed_filename
    material_repository.save_file(lesson_id, file)


def upload_file(lesson_id, file):
    save_file(lesson_id, file)

    lm = LessonMaterial()
    lm.lesson_id = lesson_id
    lm.filename =  file.filename
    lm.hashed_filename = file.hashed_filename
    lm.file_size_bytes = file.size    
    return material_repository.upload_file(lm)


def get_all_materials(lesson_id: int):
    materials = material_repository.get_all_materials(lesson_id)
    return materials


def get_material_by_filename(filename: str):
    lesson_material = material_repository.get_material_by_filename(filename)
    logger.info(f"service layer->get_material_by_filename->lesson_material = {lesson_material}")
    return lesson_material


def get_material_by_id(file_id: int):
    lesson_material = material_repository.get_material_by_id(file_id)
    logger.info(f"service layer->get_material_by_id->lesson_material = {lesson_material}")
    return lesson_material


def replace_file(file_id, file):
    file_to_replace = material_repository.get_material_by_id(file_id)
    logger.info(f"service layer->replace_file->file_to_replace={file_to_replace[0]}")
    if file_to_replace is None:
        return None
    
    hashed_filename = hash_filename(file.filename)
    file.hashed_filename = hashed_filename
    return material_repository.replace_file(file_to_replace[0], file)


def update_file(file_id, file):
    new_file_path = replace_file(file_id, file)
    if new_file_path is None:    
        return None
    
    lm = LessonMaterial()
    lm.lesson_id = int(new_file_path.parent.stem)
    lm.filename = file.filename
    lm.hashed_filename = file.hashed_filename
    lm.file_size_bytes = file.size
    return material_repository.update_file(file_id, lm)


def delete_file(file_id):
    return material_repository.delete_file(file_id)