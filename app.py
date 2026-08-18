import os
from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User, Product, Order, OrderItem
from admin import admin_bp
from flask import session, redirect, url_for, flash, request
from forms import CheckoutForm

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
    return db.session.get(User, int(user_id))


app.register_blueprint(admin_bp)


@app.context_processor
def cart_total_count():
    cart = session.get('cart', {})
    total_qty = sum(cart.values())
    return {'cart_total': total_qty}


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


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)  # или Product.query.get_or_404
    if not product:
        flash('Товар не найден', 'danger')
        return redirect(url_for('catalog'))
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f'Товар "{product.name}" добавлен в корзину', 'success')
    return redirect(request.referrer or url_for('catalog'))


@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    updated_cart = dict(cart)
    removed = False

    for product_id in list(updated_cart.keys()):
        product = db.session.get(Product, int(product_id))
        if not product:
            updated_cart.pop(product_id, None)
            removed = True

    if removed:
        session['cart'] = updated_cart
        cart = updated_cart
        flash('Некоторые товары были удалены из каталога и убраны из корзины.', 'warning')

    cart_items = []
    total = 0
    for product_id, qty in cart.items():
        product = db.session.get(Product, int(product_id))
        if product:
            subtotal = product.price * qty
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': qty,
                'subtotal': subtotal
            })

    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = session.get('cart', {})
    qty = int(request.form.get('quantity', 1))
    if qty <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = qty
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Ваша корзина пуста', 'info')
        return redirect(url_for('catalog'))

    # === Обработка исчезнувших товаров ===
    # Создаём копию корзины, чтобы безопасно изменять session['cart']
    updated_cart = dict(cart)
    removed_products = []

    for product_id in list(updated_cart.keys()):
        product = db.session.get(Product, int(product_id))
        if not product:
            # Товар удалён из базы — убираем его из корзины
            updated_cart.pop(product_id, None)
            removed_products.append(product_id)

    if removed_products:
        # Обновляем сессию
        session['cart'] = updated_cart
        cart = updated_cart

        # Уведомляем пользователя
        if len(removed_products) == 1:
            flash('Один из товаров был удалён из каталога и убран из вашей корзины.', 'warning')
        else:
            flash(
                f'Несколько товаров были удалены из каталога и убраны из вашей корзины ({len(removed_products)} шт.).',
                'warning')

        # Если корзина стала пустой — перенаправляем в каталог
        if not cart:
            flash('Все товары из вашей корзины были удалены.', 'info')
            return redirect(url_for('catalog'))
    # ===================================

    form = CheckoutForm()
    if form.validate_on_submit():
        # Пересчитываем итоговую сумму по актуальной корзине
        total = 0
        items_data = []
        for product_id, qty in cart.items():
            product = db.session.get(Product, int(product_id))
            if product:  # Дополнительная проверка на случай, если товар исчез после проверки
                subtotal = product.price * qty
                total += subtotal
                items_data.append({
                    'product': product,
                    'quantity': qty,
                    'subtotal': subtotal
                })

        # Если вдруг все товары исчезли (маловероятно, но возможно)
        if not items_data:
            session.pop('cart', None)
            flash('К сожалению, все товары в корзине недоступны. Заказ не оформлен.', 'danger')
            return redirect(url_for('catalog'))

        # Создаём заказ
        order = Order(
            customer_name=form.customer_name.data,
            customer_email=form.customer_email.data,
            customer_phone=form.customer_phone.data,
            address=form.address.data,
            comment=form.comment.data,
            total_price=total
        )
        db.session.add(order)
        db.session.flush()  # получаем order.id

        for item in items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                product_name=item['product'].name,
                price=item['product'].price,
                quantity=item['quantity']
            )
            db.session.add(order_item)

        db.session.commit()
        session.pop('cart', None)  # очищаем корзину
        flash('Заказ успешно оформлен! Мы свяжемся с вами.', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))

    # Если GET-запрос или форма не прошла валидацию — показываем корзину
    else:
        cart_items = []
        total = 0
        for product_id, qty in cart.items():
            product = db.session.get(Product, int(product_id))
        if product:
            subtotal = product.price * qty
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': qty,
                'subtotal': subtotal
            })

        return render_template('checkout.html', form=form, cart_items=cart_items, total=total)


@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order_confirmation.html', order=order)


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)
