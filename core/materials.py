from pathlib import Path

from db.models import Course, Lesson, LessonMaterial
from db.postgres import SessionLocal

BASE_DIR = Path(__file__).resolve().parent.parent
MATERIALS_DIR = BASE_DIR / "lesson_materials"


def safe_material_filename(lesson_id: int | None, index: int, ext: str) -> str:
    lesson_part = lesson_id if lesson_id is not None else "new"
    clean_ext = ext if ext.startswith(".") else f".{ext}"
    if clean_ext.lower() not in {".txt", ".docx", ".pdf"}:
        clean_ext = ".txt"
    return f"lesson_{lesson_part}_material_{index}{clean_ext}"


def ensure_material_file(material: LessonMaterial) -> None:
    if not material or not material.lesson_id or not material.hashed_filename:
        return

    folder = MATERIALS_DIR / str(material.lesson_id)
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = (material.hashed_filename or material.filename or "material.txt").replace("/", "_").replace("\\", "_")
    file_path = folder / safe_name

    if file_path.exists() and file_path.stat().st_size > 0:
        return

    title = material.filename or safe_name
    lesson_name = "Учебный урок"
    course_name = "Учебный курс"
    with SessionLocal() as db:
        lesson_obj = db.query(Lesson).filter(Lesson.id == material.lesson_id).first()
        if lesson_obj:
            lesson_name = lesson_obj.title
            course_obj = db.query(Course).filter(Course.id == lesson_obj.course_id).first()
            if course_obj:
                course_name = course_obj.name

    text = (
        "Учебная платформа\n"
        "===================\n\n"
        f"Курс: {course_name}\n"
        f"Урок: {lesson_name}\n"
        f"Материал: {title}\n\n"
        "Содержание материала:\n"
        "1. Теоретическая часть занятия.\n"
        "2. Практические задания для закрепления темы.\n"
        "3. Контрольные вопросы для самостоятельной подготовки.\n\n"
        "Материал хранится в базе данных как запись урока и скачивается из файлового хранилища платформы.\n"
    )

    if file_path.suffix.lower() == ".docx":
        import zipfile
        from html import escape

        lines = "".join(f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>" for line in text.splitlines())
        with zipfile.ZipFile(file_path, "w") as z:
            z.writestr("[Content_Types].xml", "<?xml version='1.0' encoding='UTF-8'?><Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'><Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/><Default Extension='xml' ContentType='application/xml'/><Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/></Types>")
            z.writestr("_rels/.rels", "<?xml version='1.0' encoding='UTF-8'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/></Relationships>")
            z.writestr("word/document.xml", f"<?xml version='1.0' encoding='UTF-8'?><w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body>{lines}</w:body></w:document>")
    else:
        file_path.write_text(text, encoding="utf-8")

    material.hashed_filename = safe_name
    material.file_size_bytes = file_path.stat().st_size
