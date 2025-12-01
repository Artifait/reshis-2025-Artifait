from flask import Blueprint, render_template, request, jsonify, flash, url_for, redirect
from flask_login import login_required, current_user
from typing import Optional
import secrets
import json

from domain.entities.telegram import TelegramAudit

class AdminController:
    def __init__(self, user_repo, audit_repo, chat_token_repo):
        self.user_repo = user_repo
        self.audit_repo = audit_repo
        self.chat_token_repo = chat_token_repo
        self.bp = Blueprint('admin', __name__, template_folder='../../templates')
        self._register_routes()

    def _require_admin(self):
        if not current_user.is_authenticated or not current_user.is_admin():
            return False
        return True

    def _register_routes(self):
        @self.bp.route('/users')
        @login_required
        def users_list():
            if not self._require_admin():
                flash('Доступ запрещён', 'error')
                return redirect(url_for('main.index'))
            q = (request.args.get('q') or '').strip()
            if q:
                users = self.user_repo.get_all_filtered(q)
            else:
                users = self.user_repo.get_all()
            return render_template('admin/users.html', users=users, q=q)

        @self.bp.route('/users/<int:user_id>/audit')
        @login_required
        def user_audit(user_id):
            if not self._require_admin():
                flash('Доступ запрещён', 'error')
                return redirect(url_for('main.index'))
            user = self.user_repo.get_by_id(user_id)
            if not user:
                flash('Пользователь не найден', 'error')
                return redirect(url_for('admin.users_list'))
            audits = self.audit_repo.get_by_user_id(user_id)
            return render_template('admin/user_audit.html', user=user, audits=audits)

        @self.bp.route('/users/<int:user_id>/audit/<int:audit_id>')
        @login_required
        def user_audit_detail(user_id, audit_id):
            if not self._require_admin():
                flash('Доступ запрещён', 'error')
                return redirect(url_for('main.index'))
            user = self.user_repo.get_by_id(user_id)
            if not user:
                flash('Пользователь не найден', 'error')
                return redirect(url_for('admin.users_list'))
            audit = self.audit_repo.get_by_id(audit_id)
            if not audit or int(audit.get('user_id') or 0) != user_id:
                flash('Запись аудита не найдена', 'error')
                return redirect(url_for('admin.user_audit', user_id=user_id))
            details_raw = audit.get('details') or ''
            pretty_details = details_raw
            try:
                import json
                parsed = json.loads(details_raw)
                pretty_details = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                pass
            
            return render_template('admin/user_audit_detail.html', user=user, audit=audit, pretty_details=pretty_details)

        @self.bp.route('/users/<int:user_id>/toggle-2fa', methods=['POST'])
        @login_required
        def toggle_2fa(user_id):
            if not self._require_admin():
                return jsonify({"ok": False, "message": "forbidden"}), 403
            
            enabled = request.json.get('enabled')
            enabled_bool = bool(enabled)
            # обновляем флаг 2FA
            self.user_repo.set_telegram_2fa_enabled(user_id, 1 if enabled_bool else 0)
            
            # если включаем — потребуем 2FA на следующем входе,
            # делаем это тем же способом, что и require-2fa: меняем last_login_ip на случайный
            forced_last_ip = None
            try:
                if enabled_bool:
                    import secrets
                    forced_last_ip = "10.255." + str(secrets.randbelow(254)) + "." + str(secrets.randbelow(254))
                    self.user_repo.set_last_login_ip(user_id, forced_last_ip)
            except Exception:
                forced_last_ip = None
            
            # audit
            try:
                ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                ua = request.headers.get('User-Agent')
                details_obj = {'admin_id': current_user.id, 'enabled': enabled_bool}
                if forced_last_ip:
                    details_obj['forced_last_ip'] = forced_last_ip
                details = json.dumps(details_obj, ensure_ascii=False)
                audit = TelegramAudit(id=None, user_id=user_id, event_type='admin_toggle_2fa', ip=ip, ua=ua, details=details, created_at=None)
                self.audit_repo.create(audit)
            except Exception:
                pass
            
            resp = {"ok": True, "enabled": enabled_bool}
            if forced_last_ip:
                resp['forced_last_ip'] = forced_last_ip
            return jsonify(resp)

        @self.bp.route('/users/<int:user_id>/unbind-telegram', methods=['POST'])
        @login_required
        def unbind_telegram(user_id):
            if not self._require_admin():
                return jsonify({"ok": False, "message": "forbidden"}), 403
            
            self.user_repo.set_telegram_unbound(user_id)
            tokens_removed = 0
            try:
                tokens_removed = self.chat_token_repo.unbind_tokens_by_user(user_id)
            except Exception:
                pass
            
            # audit
            try:
                ip = request.remote_addr
                ua = request.headers.get('User-Agent')
                details = json.dumps({'admin_id': current_user.id, 'tokens_removed': tokens_removed})
                audit = TelegramAudit(id=None, user_id=user_id, event_type='admin_unbind_telegram', ip=ip, ua=ua, details=details, created_at=None)
                self.audit_repo.create(audit)
            except Exception:
                pass
            
            return jsonify({"ok": True})

        @self.bp.route('/users/<int:user_id>/require-2fa', methods=['POST'])
        @login_required
        def require_2fa(user_id):
            if not self._require_admin():
                return jsonify({"ok": False, "message": "forbidden"}), 403
            
            rand_ip = "10.255." + str(secrets.randbelow(254)) + "." + str(secrets.randbelow(254))
            self.user_repo.set_last_login_ip(user_id, rand_ip)
            
            # audit
            try:
                ip = request.remote_addr
                ua = request.headers.get('User-Agent')
                details = json.dumps({'admin_id': current_user.id, 'forced_last_ip': rand_ip})
                audit = TelegramAudit(id=None, user_id=user_id, event_type='admin_force_2fa', ip=ip, ua=ua, details=details, created_at=None)
                self.audit_repo.create(audit)
            except Exception:
                pass
            
            return jsonify({"ok": True, "forced_last_ip": rand_ip})

    def get_blueprint(self):
        return self.bp
