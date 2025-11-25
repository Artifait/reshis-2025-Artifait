from flask import Blueprint, render_template, redirect, url_for
from application.services.student_service import StudentService


class MainController:
    
    def __init__(self, student_service: StudentService):
        self.student_service = student_service
        self.bp = Blueprint('main', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/')
        def index():
            from flask_login import current_user
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            students = self.student_service.get_all_students(current_user)

            students_mean = {}
            try:
                if current_user.is_teacher() or current_user.is_admin():
                    for s in students:
                        sid = getattr(s, 'id', None)
                        if sid is None:
                            students_mean[sid] = None
                            continue
                        students_mean[sid] = self.student_service.get_student_mean(sid)
            except Exception:
                students_mean = {}

            return render_template('index.html', students=students, students_mean=students_mean)
    
    def get_blueprint(self):
        return self.bp
