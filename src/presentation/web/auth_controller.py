from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from application.services.auth_service import AuthService
from application.services.telegram_service import TelegramService
from domain.entities.user import UserRole
from presentation.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm


class AuthController:
    
    def __init__(self, auth_service: AuthService, telegram_service: TelegramService | None = None):
        self.auth_service = auth_service
        self.telegram_service = telegram_service
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
            try:
                if self.telegram_service and self.telegram_service.chat_token_repo:
                    token_row = self.telegram_service.chat_token_repo.get_by_user_id(current_user.id)
                    if token_row and token_row.username:
                        setattr(current_user, 'telegram_username', token_row.username)
            except Exception:
                pass
            return render_template('auth/profile.html', user=current_user)

        @self.bp.route('/change_password', methods=['GET', 'POST'])
        @login_required
        def change_password():
            form = ChangePasswordForm()
            
            if form.validate_on_submit():
                if not current_user.check_password(form.current_password.data):
                    flash('Неверный текущий пароль', 'error')
                else:
                    current_user.set_password(form.new_password.data)
                    try:
                        self.auth_service.user_repo.update(current_user)
                    except Exception:
                        pass
                    flash('Пароль успешно изменен', 'success')
                    return redirect(url_for('auth.profile'))
            
            return render_template('auth/change_password.html', form=form)

        @self.bp.route('/setup_relationships')
        @login_required
        def setup_relationships():
            return render_template('auth/setup_relationships.html', user=current_user)
        

        # ---------------------------
        # Telegram verify & unbind endpoints (webhook token flow)
        # ---------------------------
        @self.bp.route('/profile/telegram/verify', methods=['POST'])
        @login_required
        def profile_telegram_verify():
            """
            Принимает JSON: { "token": "<TOKEN>" }
            Привязывает текущего пользователя к chat_id, если token валидный и еще не занят.
            """
            if not self.telegram_service:
                return jsonify({"ok": False, "message": "Telegram сервис не настроен"}), 500
            
            data = request.get_json() or {}
            token = (data.get('token') or '').strip()
            success, message = self.telegram_service.bind_user_with_token(current_user, token)
            if success:
                flash(message, 'success')
                return jsonify({"ok": True, "message": message}), 200
            else:
                return jsonify({"ok": False, "message": message}), 400
        
        
        @self.bp.route('/profile/telegram/unbind', methods=['POST'])
        @login_required
        def profile_telegram_unbind():
            """
            POST: открепить telegram от текущего пользователя.
            Обнуляем users.telegram_id, выключаем telegram_2fa_enabled и освобождаем token-строки.
            """
            try:
                # очистим поля в users
                current_user.telegram_id = None
                current_user.telegram_2fa_enabled = False
                # обновляем пользователя в репозитории (AuthService должен иметь user_repo)
                try:
                    self.auth_service.user_repo.update(current_user)
                except Exception:
                    pass
                
                # освобождаем все токены, связанные с этим user_id
                try:
                    if self.telegram_service and self.telegram_service.chat_token_repo:
                        self.telegram_service.chat_token_repo.unbind_tokens_by_user(current_user.id)
                except Exception:
                    pass
            
            except Exception:
                pass
            
            flash('Telegram успешно откреплен', 'success')
            return jsonify({"ok": True, "message": "Откреплено"}), 200
    
    def get_blueprint(self):
        return self.bp
