from flask import Blueprint, render_template
from flask_login import login_required
from application.services.student_service import StudentService


class ReportsController:
    
    def __init__(self, student_service: StudentService):
        self.student_service = student_service
        self.bp = Blueprint('reports', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/reports')
        @login_required
        def reports():
            from flask_login import current_user
            
            # Получаем всех студентов для отчетов
            students = self.student_service.get_all_students(current_user)
            
            return render_template('reports.html', students=students)
    
    def get_blueprint(self):
        return self.bp
