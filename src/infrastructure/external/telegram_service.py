import requests
from flask import current_app


class TelegramService:
    """
    Простой сервис для отправки сообщений через Telegram Bot API.
    Ожидает, что токен бота будет доступен в current_app.config['TELEGRAM_BOT_TOKEN']
    """

    def __init__(self, bot_token: str | None = None):
        self.bot_token = bot_token or current_app.config.get('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise RuntimeError('TELEGRAM_BOT_TOKEN is not configured')
        self.api_url = f'https://api.telegram.org/bot{self.bot_token}'

    def _log_response(self, r):
        try:
            current_app.logger.debug("Telegram response status: %s, body: %s", r.status_code, r.text)
        except Exception:
            pass

    def send_message(self, chat_id: str | int, text: str) -> bool:
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        try:
            current_app.logger.debug("Telegram send_message -> %s payload=%s", url, payload)
            r = requests.post(url, json=payload, timeout=5)
            self._log_response(r)

            if r.status_code == 200:
                return True

            # логируем тело — там бывает {"ok":false,"error_code":404,"description":"Not Found"}
            try:
                body = r.json()
            except Exception:
                body = r.text

            if r.status_code in (400, 403):
                current_app.logger.warning('Telegram send_message failed %s: %s', r.status_code, body)
                return False

            if r.status_code == 404:
                # Подсказка для разработчика — скорее всего токен/URL
                current_app.logger.error('Telegram send_message unexpected 404: %s. Проверьте TELEGRAM_BOT_TOKEN и api_url (%s)', body, self.api_url)
                # пробуем проверить getMe для диагностки
                try:
                    gm = requests.get(f"{self.api_url}/getMe", timeout=5)
                    current_app.logger.error("Telegram getMe status=%s body=%s", gm.status_code, gm.text)
                except Exception as ex:
                    current_app.logger.exception("Не удалось выполнить Telegram getMe: %s", ex)
                return False

            current_app.logger.error('Telegram send_message unexpected %s: %s', r.status_code, body)
            return False

        except requests.RequestException as e:
            current_app.logger.exception('Telegram send_message exception: %s', e)
            return False
