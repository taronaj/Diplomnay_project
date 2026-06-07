from db.models import Attendance
from pkg.repositories import attendances as attendances_repository
from schemas.attendance import AttendanceSchema
from pkg.services.user import admin_or_mentor_permission_check
from pkg.services.course_members import course_members


def get_all_attendances(course_id: int):
    attendances = attendances_repository.get_all_attendances(course_id)
    return attendances


def get_attendance_by_id(attendance_id):
    attendance = attendances_repository.get_attendance_by_id(attendance_id)
    return attendance


def create_attendance(user_id: int, attendance: AttendanceSchema):
    if admin_or_mentor_permission_check(user_id):
        return [{"error": "You are not allowed to create attendance"}]

    is_course_user = False
    for member in course_members(attendance.course_id):

        if attendance.user_id == member["id"]:
            is_course_user = True
            break

    if not is_course_user:
        return [{"error": "User is not in course members"}, False]

    a = Attendance()
    a.user_id = attendance.user_id
    a.lesson_id = attendance.lesson_id
    a.course_id = attendance.course_id
    return attendances_repository.create_attendance(a)


def update_attendance(user_id, attendance_id, attendance: AttendanceSchema):
    if admin_or_mentor_permission_check(user_id):
        return {"error": "You are not allowed to update attendance"}

    if attendance.user_id is not None or attendance.user_id != 0:
        is_course_user = False
        for member in course_members(attendance.course_id):
            if attendance.user_id == member["id"]:
                is_course_user = True
                break

        if not is_course_user:
            return {"error": "User is not in course members"}

    a = Attendance()
    a.user_id = attendance.user_id
    a.lesson_id = attendance.lesson_id
    a.attended = attendance.attended
    return attendances_repository.update_attendance(user_id, attendance_id, attendance)


def delete_attendance(user_id, attendance_id):
    if admin_or_mentor_permission_check(user_id):
        return "You are not allowed to delete attendance"
    attendance = attendances_repository.delete_attendance(user_id, attendance_id)
    return attendance
