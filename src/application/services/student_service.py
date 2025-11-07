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
        
        return {
            'student': student,
            'grades': grades,
            'attendance': attendance,
            'schedule': schedule,
            'subjects': subjects
        }
    
    def add_grade(self, student_id: int, subject_id: int, grade: int, 
                  comment: str, current_user) -> Grade | None:
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
    
