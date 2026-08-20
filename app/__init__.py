import os
from flask import Flask
from .config import Config
from .extensions import db, login_manager, migrate, cache, csrf
from .utils import create_upload_folder


def create_app(config_class=Config):
    """Фабрика приложения"""
    app = Flask(__name__, static_folder='../static',
                static_url_path='/static')
    app.config.from_object(config_class)

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)  # если используете CSRF

    # Создаём папку для загрузок (если её нет)
    create_upload_folder(app)

    # Регистрация blueprints
    from .main.routes import main_bp
    from .admin.routes import admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Загрузка пользователя для Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app
