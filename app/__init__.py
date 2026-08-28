import os
from flask import Flask, render_template
from .config import Config
from .extensions import db, login_manager, migrate, cache, csrf, mail
from .utils import create_upload_folder, init_email_settings


def create_app(config_class=Config):
    app = Flask(__name__,
                static_folder='../static',
                static_url_path='/static')
    app.config.from_object(config_class)

    # Инициализация расширений
    db.init_app(app)
    init_email_settings(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)


    # Создание папки для загрузок
    create_upload_folder(app)

    # Blueprints
    from .main.routes import main_bp
    from .admin.routes import admin_bp
    from .auth.routes import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Загрузка пользователя для Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

    # Обработчик ошибки 403
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    return app
