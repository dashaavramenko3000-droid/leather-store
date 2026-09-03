from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_assets import Environment, Bundle

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()
csrf = CSRFProtect()
mail = Mail()
compress = Compress()
assets = Environment()

# Определяем бандлы
assets.register('main_css', Bundle(
    'css/style.css',
    filters='cssmin',
    output='gen/main.min.css'
))

assets.register('main_js', Bundle(
    'js/main.js',
    filters='jsmin',
    output='gen/main.min.js'
))
