import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from application.services.auth_service import AuthService
from application.services.telegram_service import TelegramService
from domain.entities.user import UserRole
from presentation.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm

from domain.entities.telegram import TelegramAudit


class AuthController:
    
    def __init__(self, auth_service: AuthService, telegram_service: TelegramService | None = None, audit_repo=None):
        self.auth_service = auth_service
        self.telegram_service = telegram_service
        self.audit_repo = audit_repo
        self.bp = Blueprint('auth', __name__)
        self._register_routes()
    
    def _create_audit(self, user_id, event_type: str, ip: str | None, ua: str | None, details: dict | str | None = None):
        try:
            details_s = ''
            if details is not None:
                details_s = json.dumps(details) if isinstance(details, dict) else str(details)
            
            audit = TelegramAudit(
                id=None,
                user_id=user_id,
                event_type=event_type,
                ip=ip,
                ua=ua,
                details=details_s,
                created_at=None
            )
            if self.audit_repo:
                self.audit_repo.create(audit)
        except Exception:
            pass
    
    def _register_routes(self):
        
        @self.bp.route('/login', methods=['GET', 'POST'])
        def login():
            form = LoginForm()
            if form.validate_on_submit():
                user = self.auth_service.authenticate_user(form.username.data, form.password.data)
                from flask import request as flask_request
                current_ip = flask_request.remote_addr or '0.0.0.0'
                ua = flask_request.headers.get('User-Agent')
                
                if user:
                    last_ip = getattr(user, 'last_login_ip', None)
                    telegram_enabled = bool(getattr(user, 'telegram_2fa_enabled', True))
                    token_row = None
                    try:
                        token_row = self.telegram_service.chat_token_repo.get_by_user_id(user.id) if self.telegram_service else None
                    except Exception:
                        token_row = None
                    has_chat = bool(token_row)
                    
                    if last_ip and last_ip != current_ip and telegram_enabled and has_chat:
                        try:
                            verif = self.telegram_service.create_login_verification(user, current_ip)
                            token = verif.token if verif else ''
                        except Exception:
                            token = ''
                            verif = None
                        # audit: login request (2FA) sent
                        self._create_audit(user.id, 'login_request_sent', current_ip, ua, {'token': token})
                        return render_template('auth/wait_confirmation.html', token=token)
                    else:
                        # normal login
                        from flask_login import login_user
                        login_user(user, remember=form.remember_me.data)
                        user.last_login_ip = current_ip
                        try:
                            self.auth_service.user_repo.update(user)
                        except Exception:
                            pass
                        # audit: login success
                        self._create_audit(user.id, 'login_success', current_ip, ua, None)
                        flash('Вы успешно вошли в систему!', 'success')
                        return redirect(url_for('main.index'))
                else:
                    # audit: failed login attempt
                    self._create_audit(None, 'login_failed', flask_request.remote_addr or '0.0.0.0',
                                       flask_request.headers.get('User-Agent'),
                                       {'username': form.username.data})
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
                        # audit: password change
                        from flask import request as flask_request
                        self._create_audit(current_user.id, 'password_changed', flask_request.remote_addr or '0.0.0.0',
                                           flask_request.headers.get('User-Agent'), None)
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
            Обнуляем users.telegram_id и освобождаем token-строки.
            """
            try:
                # очистим поля в users
                current_user.telegram_id = None
                try:
                    self.auth_service.user_repo.update(current_user)
                except Exception:
                    pass
                
                # освобождаем все токены, связанные с этим user_id
                try:
                    if self.telegram_service and self.telegram_service.chat_token_repo:
                        removed = self.telegram_service.chat_token_repo.unbind_tokens_by_user(current_user.id)
                    else:
                        removed = None
                except Exception:
                    removed = None
                
                # audit: user unbound their telegram
                from flask import request as flask_request
                self._create_audit(current_user.id, 'user_unbind_telegram', flask_request.remote_addr or '0.0.0.0',
                                   flask_request.headers.get('User-Agent'), {'tokens_removed': removed})
            
            except Exception:
                pass
            
            flash('Telegram успешно откреплен', 'success')
            return jsonify({"ok": True, "message": "Откреплено"}), 200
        
        @self.bp.route('/login/poll')
        def login_poll():
            token = (request.args.get('token') or '').strip()
            if not token:
                return jsonify({"ok": False, "message": "token required"}), 400
            try:
                # expire old ones first
                if self.telegram_service and self.telegram_service.chat_verification_repo:
                    self.telegram_service.chat_verification_repo.expire_old()
                ver = self.telegram_service.chat_verification_repo.get_by_token(token)
                if not ver:
                    return jsonify({"ok": False, "message": "not found"}), 404
                return jsonify({"ok": True, "status": ver.status})
            except Exception as e:
                return jsonify({"ok": False, "message": str(e)}), 500
        
        @self.bp.route('/login/finish', methods=['POST'])
        def login_finish():
            data = request.get_json() or {}
            token = (data.get('token') or '').strip()
            if not token:
                return jsonify({"ok": False, "message": "token required"}), 400
            try:
                ver = self.telegram_service.chat_verification_repo.get_by_token(token)
                if not ver:
                    return jsonify({"ok": False, "message": "verification not found"}), 404
                if ver.status != 'confirmed':
                    return jsonify({"ok": False, "message": "not confirmed"}), 400
                # OK — login user
                user = self.auth_service.user_repo.get_by_id(ver.user_id)
                if not user:
                    return jsonify({"ok": False, "message": "user not found"}), 404
                from flask_login import login_user
                login_user(user)
                # update last_login_ip from verification
                try:
                    user.last_login_ip = ver.ip
                    self.auth_service.user_repo.update(user)
                except Exception:
                    pass
                
                # audit: login confirmed via telegram
                from flask import request as flask_request
                self._create_audit(user.id, 'login_confirmed', flask_request.remote_addr or '0.0.0.0',
                                   flask_request.headers.get('User-Agent'), {'token': token})
                
                return jsonify({"ok": True, "redirect": url_for('main.index')})
            except Exception as e:
                return jsonify({"ok": False, "message": str(e)}), 500
    
    def get_blueprint(self):
        return self.bp
