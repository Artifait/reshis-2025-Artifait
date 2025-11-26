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
from domain.repositories.user_repository import IUserRepository
from application.services.auth_service import AuthService
from infrastructure.external.telegram_service import TelegramService

class StudentService:
    
    def __init__(self,
                 student_repo: IStudentRepository,
                 grade_repo: IGradeRepository,
                 attendance_repo: IAttendanceRepository,
                 schedule_repo: IScheduleRepository,
                 subject_repo: ISubjectRepository,
                 auth_service: AuthService,
                 user_repo: IUserRepository,                       
                 telegram_service: TelegramService | None = None): 
        self.student_repo = student_repo
        self.grade_repo = grade_repo
        self.attendance_repo = attendance_repo
        self.schedule_repo = schedule_repo
        self.subject_repo = subject_repo
        self.auth_service = auth_service
        self.user_repo = user_repo
        self.telegram_service = telegram_service

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
        from datetime import date
        # Базовые проверки доступа
        if not current_user or not hasattr(current_user, 'id'):
            return None

        if not self.auth_service.can_edit_student_data(current_user, student_id):
            return None

        # Создаём объект и сохраняем
        new_grade = Grade(
            id=None,
            student_id=student_id,
            subject_id=subject_id,
            grade=grade,
            date=date.today(),
            comment=comment
        )

        created = self.grade_repo.create(new_grade)
        if not created:
            return None
        student = self.student_repo.get_by_id(student_id)
        if student:
            user = self.user_repo.get_by_id(student.user_id)
            telegram_id = user.telegram_id

        try:
            from markupsafe import escape
        except Exception:
            def escape(x): return str(x).replace('<', '&lt;').replace('>', '&gt;')
        
        emoji_map = {
            2: "😢",
            3: "😐",
            4: "🙂",
            5: "😄"
        }
        emoji = emoji_map.get(grade, "")

        subj_name = self.subject_repo.get_by_id(subject_id).name
        grade_str = f"{escape(str(created.grade))} {emoji}"
        date_str = created.date.strftime('%d.%m.%Y') if getattr(created, 'date', None) else ''
        comment_text = escape(created.comment or '-')
        text = (
            "📚 <b>Новая оценка!</b>\n\n"
            f"Предмет: {escape(subj_name)}\n"
            f"Оценка: {grade_str}\n"
            f"Дата: {date_str}\n"
            f"Комментарий: {comment_text}"
        )
        
        sent = self.telegram_service.send_message(telegram_id, text)
        
        if not sent:
            from flask import current_app
            current_app.logger.warning('Telegram-сообщение не отправлено пользователю %s', telegram_id)
            
        return created
    
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
    
