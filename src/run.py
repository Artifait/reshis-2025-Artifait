import os
from flask import Flask
from flask_login import LoginManager

# Infrastructure
from infrastructure.database.connection import DatabaseConnection
from infrastructure.database.schema import CREATE_TABLES_SQL, INDEXES_SQL

# Repositories
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.subject_repository import SubjectRepository
from infrastructure.repositories.grade_repository import GradeRepository
from infrastructure.repositories.attendance_repository import AttendanceRepository
from infrastructure.repositories.schedule_repository import ScheduleRepository

# Application Services
from application.services.auth_service import AuthService
from application.services.student_service import StudentService

# External services
from infrastructure.external.telegram_service import TelegramService

# Controllers
from presentation.web.main_controller import MainController
from presentation.web.student_controller import StudentController
from presentation.web.auth_controller import AuthController
from presentation.web.reports_controller import ReportsController

# Domain entities
from domain.entities.user import User


class CleanArchitectureApp:
    
    def __init__(self):
        self.app = None
        self.db_connection = None
        self.repositories = {}
        self.services = {}
        self.controllers = {}
        self.login_manager = LoginManager()
    
    def create_app(self):
        # Получаем путь к корневой папке проекта
        basedir = os.path.abspath(os.path.dirname(__file__))
        
        self.app = Flask(__name__, 
                        template_folder=os.path.join(basedir, 'templates'),
                        static_folder=os.path.join(basedir, 'static'))
        
        # Конфигурация
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
        # Поддержка конфигурации для TELEGRAM_BOT_TOKEN (если задано в окружении)
        self.app.config['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN')
        
        # Инициализация базы данных
        self._init_database()
        
        # Инициализация репозиториев
        self._init_repositories()
        
        # Инициализация сервисов
        self._init_services()
        
        # Инициализация контроллеров
        self._init_controllers()
        
        # Настройка Flask-Login
        self._init_login_manager()
        
        # Регистрация маршрутов
        self._register_blueprints()
        
        return self.app
    
    def _init_database(self):
        self.db_connection = DatabaseConnection()
        
        # Создание таблиц
        with self.db_connection.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
            conn.executescript(INDEXES_SQL)
    
    def _init_repositories(self):
        self.repositories = {
            'user': UserRepository(self.db_connection),
            'student': StudentRepository(self.db_connection),
            'subject': SubjectRepository(self.db_connection),
            'grade': GradeRepository(self.db_connection),
            'attendance': AttendanceRepository(self.db_connection),
            'schedule': ScheduleRepository(self.db_connection),
        }
    
    def _init_services(self):
        self.services = {
            'auth': AuthService(
                self.repositories['user'],
                self.repositories['student']
            ),
        }

        # Инициализируем TelegramService лишь при наличии токена, иначе оставляем None
        telegram_service = None
        token = self.app.config.get('TELEGRAM_BOT_TOKEN')
        if token:
            try:
                telegram_service = TelegramService(bot_token=token)
                self.app.logger.info('TelegramService initialized')
            except Exception as ex:
                # Не фатально — продолжаем работу без уведомлений, но фиксируем в логе
                self.app.logger.exception('Не удалось инициализировать TelegramService: %s', ex)
        else:
            self.app.logger.warning('TELEGRAM_BOT_TOKEN не задан — Telegram-уведомления отключены')

        # Student service зависит от auth service и (опционально) telegram_service
        self.services['student'] = StudentService(
            self.repositories['student'],
            self.repositories['grade'],
            self.repositories['attendance'],
            self.repositories['schedule'],
            self.repositories['subject'],
            self.services['auth'],
            self.repositories['user'],
            telegram_service
        )
    
    def _init_controllers(self):
        self.controllers = {
            'main': MainController(self.services['student']),
            'student': StudentController(self.services['student']),
            'auth': AuthController(self.services['auth']),
            'reports': ReportsController(self.services['student'])
        }
    
    def _init_login_manager(self):
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = 'auth.login'
        self.login_manager.login_message = 'Необходимо войти в систему для доступа к этой странице'
        self.login_manager.login_message_category = 'error'
        
        @self.login_manager.user_loader
        def load_user(user_id):
            user = self.repositories['user'].get_by_id(int(user_id))
            if user and user.is_student():
                # Загружаем профиль студента для пользователей с ролью student
                student_profile = self.repositories['student'].get_by_user_id(user.id)
                user.student_profile = student_profile
            return user
    
    def _register_blueprints(self):
        self.app.register_blueprint(self.controllers['main'].get_blueprint())
        self.app.register_blueprint(self.controllers['student'].get_blueprint(), url_prefix='/student')
        self.app.register_blueprint(self.controllers['auth'].get_blueprint(), url_prefix='/auth')
        self.app.register_blueprint(self.controllers['reports'].get_blueprint(), url_prefix='/reports')


def create_app():
    app_factory = CleanArchitectureApp()
    return app_factory.create_app()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
