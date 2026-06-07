from fastapi import APIRouter

from pkg.services import student_performance as students_performance_service

router = APIRouter(prefix='/student-performance', tags=['Аналитика'])


@router.get("/{course_id}/{student_id}", summary="Получить аналитику студента")
def get_student_performance(course_id: int, student_id: int):
    attendance_rate = students_performance_service.attendance_rate(course_id, student_id)
    homework_rate = students_performance_service.homework_rate(course_id, student_id)
    return {
        "attendance_rate": attendance_rate,
        "homework_rate": homework_rate
    }
