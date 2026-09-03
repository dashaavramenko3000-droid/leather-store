import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')  # TODO: сменить!
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///leather_store.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 МБ

    # Кэширование статики
    SEND_FILE_MAX_AGE_DEFAULT = 0  # 1 год = 31536000

    # Настройки Redis-Caching (для некритичных данных)
    # CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache') Раскамитить для продакшена
    CACHE_TYPE = 'SimpleCache'
    CACHE_REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    CACHE_REDIS_DB = 0
    CACHE_REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    CACHE_DEFAULT_TIMEOUT = 300  # 5 минут по умолчанию

    # Включение CSRF-защиты (рекомендуется)
    WTF_CSRF_ENABLED = True

    # Отладка
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 МБ
