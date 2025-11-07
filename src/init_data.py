import json
import os
from datetime import datetime, date, time

from run import create_app
from domain.entities.user import User, UserRole
from domain.entities.student import Student
from domain.entities.subject import Subject
from domain.entities.grade import Grade
from domain.entities.attendance import Attendance
from domain.entities.schedule import Schedule


def load_seed_data():
    seed_file = os.path.join(os.path.dirname(__file__), 'seed.json')
    with open(seed_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def init_database():
    app = create_app()
    
    with app.app_context():
        # Получаем репозитории из контекста приложения
        from run import CleanArchitectureApp
        app_factory = CleanArchitectureApp()
        app_factory._init_database()
        app_factory._init_repositories()
        
        user_repo = app_factory.repositories['user']
        student_repo = app_factory.repositories['student']
        subject_repo = app_factory.repositories['subject']
        grade_repo = app_factory.repositories['grade']
        attendance_repo = app_factory.repositories['attendance']
        schedule_repo = app_factory.repositories['schedule']
        
        # Проверяем, есть ли уже данные
        if user_repo.get_all():
            print("База данных уже содержит данные")
            return
        
        seed_data = load_seed_data()
        
        # Создаем пользователей
        users_dict = {}
        for user_data in seed_data['users']:
            user = User(
                id=None,
                username=user_data['username'],
                email=user_data['email'],
                password_hash="",  # Будет установлен через set_password
                role=UserRole(user_data['role']),
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_active=True,
                created_at=datetime.utcnow()
            )
            user.set_password(user_data['password'])
            user = user_repo.create(user)
            users_dict[user_data['username']] = user
        
        # Создаем учеников
        students_dict = {}
        for student_data in seed_data['students']:
            student = Student(
                id=None,
                name=student_data['name'],
                class_name=student_data['class_name'],
                user_id=None,
                created_at=datetime.utcnow()
            )
            student = student_repo.create(student)
            students_dict[student_data['name']] = student
        
        # Создаем предметы
        subjects_dict = {}
        for subject_data in seed_data['subjects']:
            subject = Subject(
                id=None,
                name=subject_data['name'],
                teacher=subject_data['teacher']
            )
            subject = subject_repo.create(subject)
            subjects_dict[subject_data['name']] = subject
        
        # Создаем расписание
        for schedule_data in seed_data['schedule']:
            subject = subjects_dict[schedule_data['subject_name']]
            schedule = Schedule(
                id=None,
                subject_id=subject.id,
                day_of_week=schedule_data['day_of_week'],
                time_start=time.fromisoformat(schedule_data['time_start']),
                time_end=time.fromisoformat(schedule_data['time_end']),
                classroom=schedule_data['classroom']
            )
            schedule_repo.create(schedule)
        
        # Создаем оценки
        for grade_data in seed_data['grades']:
            student = students_dict[grade_data['student_name']]
            subject = subjects_dict[grade_data['subject_name']]
            grade = Grade(
                id=None,
                student_id=student.id,
                subject_id=subject.id,
                grade=grade_data['grade'],
                date=date.fromisoformat(grade_data['date']),
                comment=grade_data.get('comment', '')
            )
            grade_repo.create(grade)
        
        # Создаем записи о посещаемости
        for attendance_data in seed_data['attendance']:
            student = students_dict[attendance_data['student_name']]
            subject = subjects_dict[attendance_data['subject_name']]
            attendance = Attendance(
                id=None,
                student_id=student.id,
                subject_id=subject.id,
                date=date.fromisoformat(attendance_data['date']),
                present=attendance_data['present'],
                reason=attendance_data.get('reason', '')
            )
            attendance_repo.create(attendance)
        
        # Создаем связи между пользователями
        relationships = seed_data.get('relationships', {})
        
        # Связь студент-пользователь
        for su_data in relationships.get('student_user', []):
            student = students_dict.get(su_data['student_name'])
            user = users_dict.get(su_data['user_username'])
            if student and user:
                student.user_id = user.id
                student_repo.update(student)
        
        print("✅ База данных инициализирована с данными из seed.json")
        print_credentials()


def print_credentials():
    print("\n" + "="*50)
    print("ТЕСТОВЫЕ УЧЕТНЫЕ ДАННЫЕ")
    print("="*50)
    print("Администратор:")
    print("  Логин: admin")
    print("  Пароль: admin123")
    print()
    print("Учитель:")
    print("  Логин: teacher1")
    print("  Пароль: teacher123")
    print()
    print("Родитель:")
    print("  Логин: parent1")
    print("  Пароль: parent123")
    print()
    print("Школьник:")
    print("  Логин: student1")
    print("  Пароль: student123")
    print("="*50)


if __name__ == '__main__':
    init_database()
