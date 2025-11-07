from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from application.services.student_service import StudentService


class StudentController:
    
    def __init__(self, student_service: StudentService):
        self.student_service = student_service
        self.bp = Blueprint('students', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/<int:student_id>')
        @login_required
        def student_diary(student_id):
            from flask_login import current_user
            
            data = self.student_service.get_student_diary_data(student_id, current_user)
            if data is None:
                flash('У вас нет прав для просмотра данных этого студента', 'error')
                return redirect(url_for('main.index'))
            return render_template('student_diary.html', **data)

        @self.bp.route('/<int:student_id>/add_grade', methods=['POST'])
        @login_required
        def add_grade(student_id):
            from flask_login import current_user
            
            subject_id = request.form['subject_id']
            grade = request.form['grade']
            comment = request.form.get('comment', '')
            
            result = self.student_service.add_grade(student_id, int(subject_id), int(grade), comment, current_user)
            if result:
                flash('Оценка добавлена успешно!', 'success')
            else:
                flash('У вас нет прав для добавления оценок', 'error')
            return redirect(url_for('students.student_diary', student_id=student_id))

        @self.bp.route('/<int:student_id>/add_attendance', methods=['POST'])
        @login_required
        def add_attendance(student_id):
            from flask_login import current_user
            
            subject_id = request.form['subject_id']
            present = 'present' in request.form
            reason = request.form.get('reason', '')
            
            result = self.student_service.add_attendance(student_id, int(subject_id), present, reason, current_user)
            if result:
                flash('Посещаемость отмечена!', 'success')
            else:
                flash('У вас нет прав для отметки посещаемости', 'error')
            return redirect(url_for('students.student_diary', student_id=student_id))

    
    def get_blueprint(self):
        return self.bp
