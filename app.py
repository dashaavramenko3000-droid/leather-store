import os
from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User, Product
from admin import admin_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
# По умолчанию SQLite для локальной разработки, в продакшене задаётся DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///leather_store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки для загрузки изображений
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к админ-панели.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(admin_bp)


@app.route('/')
def home():
    types = db.session.query(Product.product_type).distinct().all()
    latest_by_type = []
    for t in types:
        product = Product.query.filter_by(product_type=t[0]).order_by(Product.id.desc()).first()
        if product:
            latest_by_type.append(product)
    return render_template('index.html', products=latest_by_type)


@app.route('/catalog')
def catalog():
    product_type = request.args.get('type', '')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)

    query = Product.query

    if product_type:
        query = query.filter(Product.product_type == product_type)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    products = query.all()
    types = [t[0] for t in db.session.query(Product.product_type).distinct().all()]
    return render_template('catalog.html',
                           products=products,
                           current_type=product_type,
                           min_price=min_price,
                           max_price=max_price,
                           types=types)


# Создание таблиц и администратора
with app.app_context():
    # Создаём папку для загрузок, если её нет
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print('Создан пользователь admin с паролем admin123')

# Создание папки для загрузок
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)
