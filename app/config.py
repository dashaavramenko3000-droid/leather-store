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