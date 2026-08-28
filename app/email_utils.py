from flask import render_template, current_app
from flask_mail import Message
from .extensions import mail
import threading


def send_email(subject, recipients, template, **kwargs):
    """
    Отправляет email в отдельном потоке.

    :param subject: тема письма
    :param recipients: список получателей
    :param template: имя шаблона (например, 'email/order_confirmation.html')
    :param kwargs: переменные для шаблона
    """
    app = current_app._get_current_object()
    msg = Message(subject, recipients=recipients)
    # Рендерим HTML-тело
    msg.html = render_template(template, **kwargs)
    # Если нужно текстовое тело, можно добавить msg.body

    # Отправка в фоновом потоке, чтобы не блокировать основной
    thr = threading.Thread(target=_send_async, args=[app, msg])
    thr.start()


def _send_async(app, msg):
    with app.app_context():
        mail.send(msg)