from pkg.repositories import student_performance as student_performance_repositories
from logger.logger import logger


def attendance_rate(course_id: int, student_id: int):
    attendance_rate_list = student_performance_repositories.get_attendance_rate(course_id, student_id)
    if attendance_rate_list:
        attended_days = 0
        for attendance in attendance_rate_list:
            if attendance.attended:
                attended_days += 1
        attendance_rate_in_percents = 100 * (attended_days / len(attendance_rate_list))

        return round(attendance_rate_in_percents, 2)
    return 0


def homework_rate(course_id: int, student_id: int):
    homework_rate_list = student_performance_repositories.get_homework_rate(course_id, student_id)
    if homework_rate_list:
        homework_result_score = 0
        homework_days = 0
        for homework in homework_rate_list:
            if homework.score:
                homework_result_score += homework.score
                homework_days += 1
        if homework_days:
            return round(homework_result_score / homework_days, 2)
    return 0
