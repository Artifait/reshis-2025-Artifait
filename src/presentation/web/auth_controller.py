from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from application.services.auth_service import AuthService
from domain.entities.user import UserRole
from presentation.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm


class AuthController:
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.bp = Blueprint('auth', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/login', methods=['GET', 'POST'])
        def login():
            form = LoginForm()
            if form.validate_on_submit():
                # Сперва проверяем, не деактивирован ли пользователь
                user_by_name = self.auth_service.user_repo.get_by_username(form.username.data)
                if user_by_name and not user_by_name.is_active:
                    flash('Аккаунт заблокирован. Обратитесь к администратору.', 'error')
                else:
                    user = self.auth_service.authenticate_user(form.username.data, form.password.data)
                    if user:
                        from flask_login import login_user
                        login_user(user, remember=form.remember_me.data)
                        flash('Вы успешно вошли в систему!', 'success')
                        return redirect(url_for('main.index'))
                    else:
                        flash('Неверное имя пользователя или пароль', 'error')
            
            return render_template('auth/login.html', form=form)

        @self.bp.route('/logout')
        def logout():
            from flask_login import logout_user
            logout_user()
            flash('Вы вышли из системы', 'info')
            return redirect(url_for('auth.login'))

        @self.bp.route('/register', methods=['GET', 'POST'])
        def register():
            form = RegisterForm()
            if form.validate_on_submit():
                user, error = self.auth_service.register_user(
                    form.username.data, form.email.data, form.password.data, 
                    form.first_name.data, form.last_name.data, UserRole(form.role.data)
                )
                
                if user:
                    flash('Регистрация прошла успешно!', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash(f'Ошибка регистрации: {error}', 'error')
            
            return render_template('auth/register.html', form=form)

        @self.bp.route('/profile')
        @login_required
        def profile():
            from flask_login import current_user
            return render_template('auth/profile.html', user=current_user)

        @self.bp.route('/change_password', methods=['GET', 'POST'])
        @login_required
        def change_password():
            from flask_login import current_user
            form = ChangePasswordForm()
            
            if form.validate_on_submit():
                if not current_user.check_password(form.current_password.data):
                    flash('Неверный текущий пароль', 'error')
                else:
                    current_user.set_password(form.new_password.data)
                    # TODO: Обновить в репозитории
                    flash('Пароль успешно изменен', 'success')
                    return redirect(url_for('auth.profile'))
            
            return render_template('auth/change_password.html', form=form)

        @self.bp.route('/setup_relationships')
        @login_required
        def setup_relationships():
            from flask_login import current_user
            return render_template('auth/setup_relationships.html', user=current_user)
        
        @self.bp.route('/manage_users', methods=['GET', 'POST'])
        @login_required
        def manage_users():
            from flask_login import current_user
            
            # Только админ имеет доступ
            if not current_user.is_admin():
                flash('У вас нет прав для доступа к этой странице', 'error')
                return redirect(url_for('main.index'))

            # Обработка изменения статуса пользователя (POST)
            if request.method == 'POST':
                try:
                    target_id = int(request.form.get('user_id'))
                except (TypeError, ValueError):
                    flash('Неверный идентификатор пользователя', 'error')
                    return redirect(url_for('auth.manage_users'))

                action = request.form.get('action')
                if action == 'deactivate':
                    success, message = self.auth_service.set_user_active(target_id, False, current_user)
                elif action == 'activate':
                    success, message = self.auth_service.set_user_active(target_id, True, current_user)
                else:
                    success, message = False, "Неизвестное действие"

                flash(message, 'success' if success else 'error')
                return redirect(url_for('auth.manage_users'))

            # GET: показываем всех пользователей
            users = self.auth_service.user_repo.get_all()
            return render_template('auth/manage_users.html', users=users, current_user=current_user)

    def get_blueprint(self):
        return self.bp
