import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')  # TODO: сменить!
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///leather_store.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 МБ

    # Кэширование статики
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 год

    # Настройки Flask-Caching (для некритичных данных)
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # Включение CSRF-защиты (рекомендуется)
    WTF_CSRF_ENABLED = True

    # Отладка
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.yandex.ru')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your_email@yandex.ru')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'your_email@yandex.ru')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 МБ
