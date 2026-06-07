import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func

from core.materials import ensure_material_file, safe_material_filename, MATERIALS_DIR
from core.security import get_current_user, require_roles
from db.models import (
    Attendance,
    Course,
    CourseUser,
    Homework,
    Lesson,
    LessonMaterial,
    Role,
    Schedule,
    StudentPerformance,
    User,
)
from db.postgres import SessionLocal
from utils.auth import create_access_token
from utils.hash import verify_password

router = APIRouter(prefix="/frontend-api", tags=["Frontend API"], include_in_schema=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateCourseRequest(BaseModel):
    name: str
    price: int | None = 0
    description: str | None = ""


class CreateLessonRequest(BaseModel):
    course_id: int | None = None
    title: str
    description: str | None = ""


class CreateMaterialRequest(BaseModel):
    lesson_id: int | None = None
    filename: str
    file_size_bytes: int | None = 204800


class CreateHomeworkRequest(BaseModel):
    lesson_id: int | None = None
    student_id: int | None = None
    course_id: int | None = None
    score: float | None = 90
    homework: str | None = "Практическая работа"


class CreateAttendanceRequest(BaseModel):
    lesson_id: int | None = None
    user_id: int | None = None
    course_id: int | None = None
    attended: bool = True


def _role_code(role_name: str) -> str:
    name = (role_name or "").lower()
    if "админ" in name or "admin" in name:
        return "admin"
    if "преп" in name or "mentor" in name or "teacher" in name:
        return "mentor"
    return "student"


@router.get("/version")
async def frontend_version():
    return {"version": "production-refactor", "single_database": True, "jwt_dashboard": True}


@router.post("/sign-in")
async def frontend_sign_in(payload: LoginRequest):
    login = payload.username.strip().lower()
    with SessionLocal() as db:
        db_user = db.query(User).filter(User.username == login).first()
        if not db_user or not verify_password(payload.password, db_user.password):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

        db_role = db.query(Role).filter(Role.id == db_user.role_id).first()
        role = _role_code(db_role.name if db_role else "")
        access_token = create_access_token({"id": db_user.id, "role_id": db_user.role_id})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "role": role,
                "full_name": db_user.full_name or db_user.username,
            },
        }


@router.get("/dashboard-data")
async def frontend_dashboard_data(current_user=Depends(get_current_user)):
    with SessionLocal() as db:
        courses_db = db.query(Course).filter(Course.deleted_at == None).order_by(Course.id.asc()).all()
        lessons_db = db.query(Lesson).filter(Lesson.deleted_at == None).order_by(Lesson.id.asc()).all()
        materials_db = db.query(LessonMaterial).filter(LessonMaterial.deleted_at == None).order_by(LessonMaterial.id.asc()).all()
        users_db = db.query(User).order_by(User.id.asc()).all()
        roles_db = db.query(Role).order_by(Role.id.asc()).all()
        homeworks_db = db.query(Homework).filter(Homework.deleted_at == None).order_by(Homework.id.asc()).all()
        attendances_db = db.query(Attendance).order_by(Attendance.id.asc()).all()
        performances_db = db.query(StudentPerformance).order_by(StudentPerformance.id.asc()).all()
        schedules_db = db.query(Schedule).order_by(Schedule.scheduled_time.asc()).all()

        roles = {r.id: r.name for r in roles_db}
        users = {u.id: u for u in users_db}
        courses = {c.id: c for c in courses_db}
        lessons = {l.id: l for l in lessons_db}

        student_users = [u for u in users_db if "студ" in (roles.get(u.role_id, "").lower()) or "student" in (roles.get(u.role_id, "").lower())]
        mentor_users = [u for u in users_db if "преп" in (roles.get(u.role_id, "").lower()) or "mentor" in (roles.get(u.role_id, "").lower()) or "teacher" in (roles.get(u.role_id, "").lower())]

        def course_mentor(course_id: int) -> str:
            links = db.query(CourseUser).filter(CourseUser.course_id == course_id).all()
            mentor_ids = {u.id for u in mentor_users}
            for link in links:
                user = users.get(link.user_id)
                if user and user.id in mentor_ids:
                    return user.full_name or user.username
            return mentor_users[0].full_name if mentor_users else "Преподаватель"

        course_rows = []
        for course in courses_db:
            members = db.query(CourseUser).filter(CourseUser.course_id == course.id).count()
            done = db.query(Lesson).filter(Lesson.course_id == course.id, Lesson.deleted_at == None).count()
            progress = min(100, max(35, done * 20))
            course_rows.append({"id": course.id, "name": course.name, "price": course.price or 0, "description": course.description or "", "members": members, "mentor": course_mentor(course.id), "progress": progress})

        student_rows = []
        for user in student_users:
            perf = next((p for p in performances_db if p.student_id == user.id), None)
            course_name = courses.get(perf.course_id).name if perf and courses.get(perf.course_id) else "—"
            student_rows.append({"id": user.id, "name": user.full_name or user.username, "username": user.username, "course": course_name, "score": float(perf.avg_score) if perf and perf.avg_score is not None else None, "attendance": float(perf.attendance_rate) if perf and perf.attendance_rate is not None else None})

        lesson_rows = [{"id": lesson.id, "title": lesson.title, "course_id": lesson.course_id, "course": courses.get(lesson.course_id).name if courses.get(lesson.course_id) else "—", "description": lesson.description or "", "status": "Активный"} for lesson in lessons_db]
        material_rows = [{"id": material.id, "filename": material.filename or "Файл", "lesson_id": material.lesson_id, "lesson": lessons.get(material.lesson_id).title if lessons.get(material.lesson_id) else "—", "size": round((material.file_size_bytes or 0) / 1024, 1), "download_url": f"/frontend-api/materials/{material.id}/download"} for material in materials_db]

        homework_rows = []
        for homework in homeworks_db:
            homework_rows.append({
                "id": homework.id,
                "name": homework.homework or (lessons.get(homework.lesson_id).title if lessons.get(homework.lesson_id) else "Домашняя работа"),
                "lesson": lessons.get(homework.lesson_id).title if lessons.get(homework.lesson_id) else "—",
                "student_id": homework.student_id,
                "student": users.get(homework.student_id).full_name if users.get(homework.student_id) else "Студент",
                "course": courses.get(homework.course_id).name if courses.get(homework.course_id) else "—",
                "score": float(homework.score) if homework.score is not None else None,
            })

        attendance_rows = []
        for attendance in attendances_db:
            attendance_rows.append({
                "id": attendance.id,
                "student_id": attendance.user_id,
                "student": users.get(attendance.user_id).full_name if users.get(attendance.user_id) else "Студент",
                "lesson": lessons.get(attendance.lesson_id).title if lessons.get(attendance.lesson_id) else "—",
                "course": courses.get(attendance.course_id).name if courses.get(attendance.course_id) else "—",
                "status": "Присутствовал" if attendance.attended else "Отсутствовал",
                "date": attendance.attendance_date.strftime("%d.%m.%Y") if attendance.attendance_date else "—",
            })

        schedule_rows = [{"id": item.id, "course": courses.get(item.course_id).name if courses.get(item.course_id) else "—", "lesson": lessons.get(item.lesson_id).title if lessons.get(item.lesson_id) else "—", "mentor": users.get(item.mentor_id).full_name if users.get(item.mentor_id) else "Преподаватель", "time": item.scheduled_time.strftime("%d.%m.%Y %H:%M") if item.scheduled_time else "—"} for item in schedules_db]

        current_role = db.query(Role).filter(Role.id == current_user.role_id).first()
        current_role_code = _role_code(current_role.name if current_role else "")
        if current_role_code == "student":
            allowed_course_ids = {link.course_id for link in db.query(CourseUser).filter(CourseUser.user_id == current_user.id).all()}
            if not allowed_course_ids:
                allowed_course_ids = {p.course_id for p in performances_db if p.student_id == current_user.id}
            student_rows = [row for row in student_rows if row.get("id") == current_user.id]
            homework_rows = [row for row in homework_rows if row.get("student_id") == current_user.id]
            attendance_rows = [row for row in attendance_rows if row.get("student_id") == current_user.id]
            course_rows = [row for row in course_rows if row.get("id") in allowed_course_ids]
            lesson_rows = [row for row in lesson_rows if row.get("course_id") in allowed_course_ids]
            allowed_lesson_ids = {row.get("id") for row in lesson_rows}
            material_rows = [row for row in material_rows if row.get("lesson_id") in allowed_lesson_ids]

        return {
            "courses": course_rows,
            "students": student_rows,
            "lessons": lesson_rows,
            "homework": homework_rows,
            "materials": material_rows,
            "grades": homework_rows,
            "attendance": attendance_rows,
            "schedule": schedule_rows,
            "options": {
                "courses": [{"id": c.id, "name": c.name} for c in courses_db],
                "lessons": [{"id": l.id, "title": l.title, "course_id": l.course_id} for l in lessons_db],
                "students": [{"id": u.id, "name": u.full_name or u.username} for u in student_users],
                "mentors": [{"id": u.id, "name": u.full_name or u.username} for u in mentor_users],
            },
        }


@router.post("/courses")
async def frontend_create_course(payload: CreateCourseRequest, current_user=Depends(require_roles("Администратор"))):
    with SessionLocal() as db:
        course = Course(name=payload.name.strip(), price=payload.price or 0, description=payload.description or "Описание курса")
        db.add(course)
        db.commit()
        db.refresh(course)
        return {"status": "ok", "id": course.id}


@router.post("/lessons")
async def frontend_create_lesson(payload: CreateLessonRequest, current_user=Depends(require_roles("Администратор", "Преподаватель"))):
    with SessionLocal() as db:
        course = db.query(Course).filter(Course.deleted_at == None).order_by(Course.id.asc()).first()
        lesson = Lesson(course_id=payload.course_id or (course.id if course else None), title=payload.title.strip(), description=payload.description or "Описание урока")
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return {"status": "ok", "id": lesson.id}


@router.post("/materials")
async def frontend_create_material(payload: CreateMaterialRequest, current_user=Depends(require_roles("Администратор", "Преподаватель"))):
    with SessionLocal() as db:
        lesson = db.query(Lesson).filter(Lesson.deleted_at == None).order_by(Lesson.id.asc()).first()
        lesson_id = payload.lesson_id or (lesson.id if lesson else None)
        ext = Path(payload.filename).suffix or ".txt"
        material = LessonMaterial(lesson_id=lesson_id, filename=payload.filename.strip(), hashed_filename=safe_material_filename(lesson_id, 1, ext), file_size_bytes=payload.file_size_bytes or 204800)
        db.add(material)
        db.commit()
        db.refresh(material)
        ensure_material_file(material)
        db.commit()
        return {"status": "ok", "id": material.id}


@router.post("/homework")
async def frontend_create_homework(payload: CreateHomeworkRequest, current_user=Depends(require_roles("Администратор", "Преподаватель"))):
    with SessionLocal() as db:
        lesson = db.query(Lesson).filter(Lesson.id == payload.lesson_id).first() if payload.lesson_id else db.query(Lesson).filter(Lesson.deleted_at == None).order_by(Lesson.id.asc()).first()
        course_id = payload.course_id or (lesson.course_id if lesson else None)
        if not course_id:
            course = db.query(Course).filter(Course.deleted_at == None).order_by(Course.id.asc()).first()
            course_id = course.id if course else None
        student_role = db.query(Role).filter(Role.name.ilike("%Студент%")).first()
        student = db.query(User).filter(User.id == payload.student_id).first() if payload.student_id else (db.query(User).filter(User.role_id == student_role.id).first() if student_role else db.query(User).first())
        mentor_role = db.query(Role).filter(Role.name.ilike("%Преподаватель%")).first()
        mentor = db.query(User).filter(User.role_id == mentor_role.id).first() if mentor_role else None
        homework = Homework(lesson_id=lesson.id if lesson else None, student_id=student.id if student else None, course_id=course_id, mentor_id=mentor.id if mentor else None, score=payload.score, homework=payload.homework or "Домашняя работа")
        db.add(homework)
        db.commit()
        if student and course_id:
            avg = db.query(func.avg(Homework.score)).filter(Homework.student_id == student.id, Homework.course_id == course_id, Homework.deleted_at == None).scalar() or payload.score or 0
            perf = db.query(StudentPerformance).filter(StudentPerformance.student_id == student.id, StudentPerformance.course_id == course_id).first()
            if not perf:
                db.add(StudentPerformance(student_id=student.id, course_id=course_id, avg_score=avg, attendance_rate=90))
            else:
                perf.avg_score = avg
            db.commit()
        db.refresh(homework)
        return {"status": "ok", "id": homework.id}


@router.post("/attendance")
async def frontend_create_attendance(payload: CreateAttendanceRequest, current_user=Depends(require_roles("Администратор", "Преподаватель"))):
    with SessionLocal() as db:
        lesson = db.query(Lesson).filter(Lesson.id == payload.lesson_id).first() if payload.lesson_id else db.query(Lesson).filter(Lesson.deleted_at == None).order_by(Lesson.id.asc()).first()
        course_id = payload.course_id or (lesson.course_id if lesson else None)
        if not course_id:
            course = db.query(Course).filter(Course.deleted_at == None).order_by(Course.id.asc()).first()
            course_id = course.id if course else None
        student_role = db.query(Role).filter(Role.name.ilike("%Студент%")).first()
        student = db.query(User).filter(User.id == payload.user_id).first() if payload.user_id else (db.query(User).filter(User.role_id == student_role.id).first() if student_role else db.query(User).first())
        attendance = Attendance(lesson_id=lesson.id if lesson else None, user_id=student.id if student else None, course_id=course_id, attended=payload.attended, attendance_date=datetime.datetime.now())
        db.add(attendance)
        db.commit()
        if student and course_id:
            total = db.query(Attendance).filter(Attendance.user_id == student.id, Attendance.course_id == course_id).count() or 1
            present = db.query(Attendance).filter(Attendance.user_id == student.id, Attendance.course_id == course_id, Attendance.attended == True).count()
            rate = round(present * 100 / total, 2)
            perf = db.query(StudentPerformance).filter(StudentPerformance.student_id == student.id, StudentPerformance.course_id == course_id).first()
            if not perf:
                db.add(StudentPerformance(student_id=student.id, course_id=course_id, avg_score=0, attendance_rate=rate))
            else:
                perf.attendance_rate = rate
            db.commit()
        db.refresh(attendance)
        return {"status": "ok", "id": attendance.id}


@router.get("/materials/{material_id}/download")
async def frontend_download_material(material_id: int, current_user=Depends(get_current_user)):
    with SessionLocal() as db:
        material = db.query(LessonMaterial).filter(LessonMaterial.id == material_id, LessonMaterial.deleted_at == None).first()
        if not material:
            raise HTTPException(status_code=404, detail="Материал не найден")
        ensure_material_file(material)
        db.commit()
        file_path = MATERIALS_DIR / str(material.lesson_id) / material.hashed_filename
        return FileResponse(path=file_path, filename=material.filename or "material.txt", media_type="application/octet-stream")
