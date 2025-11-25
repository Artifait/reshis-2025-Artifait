from typing import Any
from datetime import date
from domain.entities.student import Student
from domain.entities.grade import Grade
from domain.entities.attendance import Attendance
from domain.entities.schedule import Schedule
from domain.entities.subject import Subject
from domain.repositories.student_repository import IStudentRepository
from domain.repositories.grade_repository import IGradeRepository
from domain.repositories.attendance_repository import IAttendanceRepository
from domain.repositories.schedule_repository import IScheduleRepository
from domain.repositories.subject_repository import ISubjectRepository
from application.services.auth_service import AuthService


class StudentService:
    
    def __init__(self, 
                 student_repo: IStudentRepository,
                 grade_repo: IGradeRepository,
                 attendance_repo: IAttendanceRepository,
                 schedule_repo: IScheduleRepository,
                 subject_repo: ISubjectRepository,
                 auth_service: AuthService):
        self.student_repo = student_repo
        self.grade_repo = grade_repo
        self.attendance_repo = attendance_repo
        self.schedule_repo = schedule_repo
        self.subject_repo = subject_repo
        self.auth_service = auth_service
    
    def get_all_students(self, current_user) -> list[Student]:
        if not current_user or not hasattr(current_user, 'id'):
            return []
        return self.auth_service.get_user_students(current_user)
    
    def get_student_by_id(self, student_id: int) -> Student | None:
        return self.student_repo.get_by_id(student_id)
    
    def get_student_diary_data(self, student_id: int, current_user) -> dict[str, Any] | None:
        if not current_user or not hasattr(current_user, 'id'):
            return None
            
        if not self.auth_service.can_view_student_data(current_user, student_id):
            return None
            
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return None
            
        grades = self.grade_repo.get_by_student(student_id)
        attendance = self.attendance_repo.get_by_student(student_id)
        schedule = self.schedule_repo.get_all()
        subjects = self.subject_repo.get_all()
        
        # Создаем словарь предметов для быстрого поиска
        subjects_dict = {subject.id: subject for subject in subjects}
        
        # Добавляем объект предмета к каждой оценке
        for grade in grades:
            grade.subject = subjects_dict.get(grade.subject_id)
        
        # Добавляем объект предмета к каждой записи посещаемости
        for att in attendance:
            att.subject = subjects_dict.get(att.subject_id)
        
        # Добавляем объект предмета к каждому элементу расписания
        for sched in schedule:
            sched.subject = subjects_dict.get(sched.subject_id)
        
        # Рассчитываем статистику оценок
        statistics = self.calculate_student_statistics(student_id, current_user)
        
        return {
            'student': student,
            'grades': grades,
            'attendance': attendance,
            'schedule': schedule,
            'subjects': subjects,
            'statistics': statistics
        }
    
    def add_grade(self, student_id: int, subject_id: int, grade: int, 
                  comment: str, current_user) -> Grade | None:
        """Добавить оценку с проверкой прав доступа"""
        if not current_user or not hasattr(current_user, 'id'):
            return None
            
        if not self.auth_service.can_edit_student_data(current_user, student_id):
            return None
            
        new_grade = Grade(
            id=None,
            student_id=student_id,
            subject_id=subject_id,
            grade=grade,
            date=date.today(),
            comment=comment
        )
        
        return self.grade_repo.create(new_grade)
    
    def add_attendance(self, student_id: int, subject_id: int, present: bool, 
                      reason: str, current_user) -> Attendance | None:
        """Добавить отметку посещаемости с проверкой прав доступа"""
        if not current_user or not hasattr(current_user, 'id'):
            return None
            
        if not self.auth_service.can_edit_student_data(current_user, student_id):
            return None
            
        new_attendance = Attendance(
            id=None,
            student_id=student_id,
            subject_id=subject_id,
            date=date.today(),
            present=present,
            reason=reason
        )
        
        return self.attendance_repo.create(new_attendance)
    
    def calculate_student_statistics(self, student_id: int, current_user) -> dict[str, Any] | None:
        grades = self.grade_repo.get_by_student(student_id)
        grade_values = [grade.grade for grade in grades if grade is not None]

        n = len(grade_values)

        if n == 0:
            return {
                'mean_grade': 0.00,
                'median_grade': 0.00,
                'total_grades': 0,
                'grade_distribution': {}
            }

        mean_grade = round(sum(grade_values) / n, 2)

        # Медиана
        sorted_grades = sorted(grade_values)
        if n % 2 == 1:
            median_grade = sorted_grades[n // 2]
        else:
            median_grade = (sorted_grades[n // 2 - 1] + sorted_grades[n // 2]) / 2
        median_grade = round(median_grade, 2)

        # Распределение оценок
        from collections import Counter
        grade_distribution = dict(Counter(grade_values))

        return {
            'mean_grade': mean_grade,
            'median_grade': median_grade,
            'total_grades': n,
            'grade_distribution': grade_distribution
        }
    
