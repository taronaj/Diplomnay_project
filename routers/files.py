from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from core.materials import MATERIALS_DIR, ensure_material_file
from db.models import LessonMaterial
from db.postgres import SessionLocal

router = APIRouter(tags=["Files"])


@router.get("/admin/material/download/{material_id}")
async def download_material(material_id: int):
    with SessionLocal() as db:
        material = db.query(LessonMaterial).filter(
            LessonMaterial.id == material_id,
            LessonMaterial.deleted_at == None,
        ).first()
        if not material:
            raise HTTPException(status_code=404, detail="Материал не найден")
        ensure_material_file(material)
        db.commit()
        file_path = MATERIALS_DIR / str(material.lesson_id) / material.hashed_filename
        return FileResponse(path=file_path, filename=material.filename or "material.txt", media_type="application/octet-stream")
