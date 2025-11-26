from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from application.services.auth_service import AuthService
from domain.entities.user import UserRole
from presentation.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm
from presentation.forms.profile_forms import ProfileForm


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
            return render_template('auth/profile.html', user=current_user)

        @self.bp.route('/profile/edit', methods=['GET', 'POST'])
        @login_required
        def edit_profile():
            """
            Редактирование профиля пользователя, включая поле Telegram ID.
            Использует ProfileForm (first_name, last_name, telegram_id, submit, delete_telegram).
            """
            form = ProfileForm(obj=current_user)

            if form.validate_on_submit():
                # Обновляем простые поля
                if form.first_name.data is not None:
                    current_user.first_name = form.first_name.data or current_user.first_name
                if form.last_name.data is not None:
                    current_user.last_name = form.last_name.data or current_user.last_name

                # Обработка удаления Telegram ID (нажатие соответствующей кнопки)
                if form.delete_telegram.data:
                    current_user.telegram_id = None
                else:
                    # Обычный submit — обновляем telegram_id (если указано), иначе не трогаем
                    # Если поле пустое, можно считать, что пользователь хочет убрать ID — но это поведение
                    # зависит от требований. Здесь мы оставляем прежний ID, если поле пустое и не нажата кнопка удаления.
                    if form.telegram_id.data:
                        current_user.telegram_id = form.telegram_id.data

                # Сохраняем через сервис (AuthService должен реализовать update_user)
                try:
                    self.auth_service.update_user(current_user)
                    flash('Профиль успешно обновлён', 'success')
                    return redirect(url_for('auth.profile'))
                except Exception as ex:
                    current_app.logger.exception('Ошибка при сохранении профиля: %s', ex)
                    flash('Не удалось сохранить профиль. Попробуйте позже.', 'error')

            # При GET — заполняем форму текущими значениями
            if request.method == 'GET':
                form.first_name.data = current_user.first_name
                form.last_name.data = current_user.last_name
                form.telegram_id.data = current_user.telegram_id

            return render_template('auth/profile_edit.html', form=form, user=current_user)

        @self.bp.route('/change_password', methods=['GET', 'POST'])
        @login_required
        def change_password():
            form = ChangePasswordForm()
            
            if form.validate_on_submit():
                if not current_user.check_password(form.current_password.data):
                    flash('Неверный текущий пароль', 'error')
                else:
                    current_user.set_password(form.new_password.data)
                    # TODO: Обновить в репозитории через сервис
                    try:
                        self.auth_service.update_user(current_user)
                    except Exception:
                        current_app.logger.exception('Ошибка при обновлении пароля')
                    flash('Пароль успешно изменен', 'success')
                    return redirect(url_for('auth.profile'))
            
            return render_template('auth/change_password.html', form=form)

        @self.bp.route('/setup_relationships')
        @login_required
        def setup_relationships():
            return render_template('auth/setup_relationships.html', user=current_user)
    
    def get_blueprint(self):
        return self.bp
