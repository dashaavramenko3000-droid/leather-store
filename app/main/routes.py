from flask import render_template, request, session, redirect, url_for, flash, jsonify, abort
from flask_login import current_user

from ..utils import save_image
from . import main_bp
from ..extensions import db
from ..models import Product, Order, OrderItem, CartItem, CustomOrder
from ..forms import CheckoutForm, CustomOrderForm


@main_bp.context_processor
def cart_total_count():
    if current_user.is_authenticated:
        total_qty = sum(item.quantity for item in CartItem.query.filter_by(user_id=current_user.id).all())
    else:
        cart = session.get('cart', {})
        total_qty = sum(cart.values())
    return {'cart_total': total_qty}


@main_bp.route('/')
def home():
    """Главная страница: показываем по одному последнему товару каждого типа."""
    types = db.session.query(Product.product_type).distinct().all()
    latest_by_type = []
    for t in types:
        product = Product.query.filter_by(product_type=t[0]).order_by(Product.id.desc()).first()
        if product:
            latest_by_type.append(product)
    return render_template('index.html', products=latest_by_type)


@main_bp.route('/catalog')
def catalog():
    """Каталог с фильтрацией по типу и цене."""
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


@main_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash('Товар не найден', 'danger')
        return redirect(url_for('main.catalog'))

    if current_user.is_authenticated:
        # Добавляем в БД
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
            db.session.add(cart_item)
        db.session.commit()
    else:
        # Добавляем в сессию
        cart = session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        session['cart'] = cart

    flash(f'Товар "{product.name}" добавлен в корзину', 'success')
    return redirect(request.referrer or url_for('main.catalog'))


@main_bp.route('/cart')
def cart():
    if current_user.is_authenticated:
        # Получаем элементы корзины пользователя
        cart_items_db = CartItem.query.filter_by(user_id=current_user.id).order_by(CartItem.created_at).all()
        cart_items = []
        total = 0
        for item in cart_items_db:
            product = item.product
            if product:
                subtotal = product.price * item.quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': item.quantity,
                    'subtotal': subtotal,
                    # 'cart_item_id': item.id  # для удаления/обновления
                })
    else:
        # Гостевая корзина (сессия)
        cart = session.get('cart', {})
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
                    'subtotal': subtotal,
                    'cart_item_id': product_id  # для гостей используем product_id
                })

    return render_template('cart.html', cart_items=cart_items, total=total)


@main_bp.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    qty = int(request.form.get('quantity', 1))
    if qty <= 0:
        qty = 0

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            if qty == 0:
                db.session.delete(cart_item)
            else:
                cart_item.quantity = qty
            db.session.commit()
    else:
        cart = session.get('cart', {})
        if qty == 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = qty
        session['cart'] = cart

    return redirect(url_for('main.cart'))


@main_bp.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
    else:
        cart = session.get('cart', {})
        cart.pop(str(product_id), None)
        session['cart'] = cart

    return redirect(url_for('main.cart'))


@main_bp.route('/cart/update_ajax/<int:product_id>', methods=['POST'])
def update_cart_ajax(product_id):
    try:
        qty = int(request.form.get('quantity', 1))
    except ValueError:
        return jsonify({'success': False, 'message': 'Некорректное количество'}), 400

    if qty < 0:
        qty = 0

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            if qty == 0:
                db.session.delete(cart_item)
            else:
                cart_item.quantity = qty
            db.session.commit()
        # Вычисляем subtotal для товара
        product = db.session.get(Product, product_id)
        subtotal = product.price * qty if product and qty > 0 else 0
        total = sum(
            item.product.price * item.quantity for item in CartItem.query.filter_by(user_id=current_user.id).all() if
            item.product)
        cart_total = sum(item.quantity for item in CartItem.query.filter_by(user_id=current_user.id).all())
    else:
        cart = session.get('cart', {})
        if qty == 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = qty
        session['cart'] = cart
        product = db.session.get(Product, product_id)
        subtotal = product.price * qty if product and qty > 0 else 0
        total = 0
        for pid, quantity in cart.items():
            p = db.session.get(Product, int(pid))
            if p:
                total += p.price * quantity
        cart_total = sum(cart.values())

    return jsonify({
        'success': True,
        'quantity': qty,
        'total': total,
        'cart_total': cart_total,
        'subtotal': subtotal
    })


@main_bp.route('/cart/remove_ajax/<int:product_id>', methods=['POST'])
def remove_from_cart_ajax(product_id):
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
        total = sum(
            item.product.price * item.quantity for item in CartItem.query.filter_by(user_id=current_user.id).all() if
            item.product)
        cart_total = sum(item.quantity for item in CartItem.query.filter_by(user_id=current_user.id).all())
    else:
        cart = session.get('cart', {})
        cart.pop(str(product_id), None)
        session['cart'] = cart
        total = 0
        for pid, quantity in cart.items():
            p = db.session.get(Product, int(pid))
            if p:
                total += p.price * quantity
        cart_total = sum(cart.values())

    return jsonify({
        'success': True,
        'total': total,
        'cart_total': cart_total,
        'removed_product_id': product_id
    })


@main_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Собираем корзину в зависимости от авторизации
    if current_user.is_authenticated:
        cart_items_db = CartItem.query.filter_by(user_id=current_user.id).all()
        cart_items = []
        total = 0
        for item in cart_items_db:
            product = item.product
            if product:
                subtotal = product.price * item.quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': item.quantity,
                    'subtotal': subtotal
                })
        if not cart_items:
            flash('Ваша корзина пуста', 'info')
            return redirect(url_for('main.catalog'))
    else:
        cart = session.get('cart', {})
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
        if not cart_items:
            flash('Ваша корзина пуста', 'info')
            return redirect(url_for('main.catalog'))

    form = CheckoutForm()
    if form.validate_on_submit():
        # Создаём заказ
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            customer_name=form.customer_name.data,
            customer_email=form.customer_email.data,
            customer_phone=form.customer_phone.data,
            address=form.address.data,
            comment=form.comment.data,
            total_price=total
        )
        db.session.add(order)
        db.session.flush()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                product_name=item['product'].name,
                price=item['product'].price,
                quantity=item['quantity']
            )
            db.session.add(order_item)

        db.session.commit()

        # Очищаем корзину
        if current_user.is_authenticated:
            CartItem.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
        else:
            session.pop('cart', None)

        flash('Заказ успешно оформлен! Мы свяжемся с вами.', 'success')
        return redirect(url_for('main.order_confirmation', order_id=order.id))

    # GET или ошибки валидации
    return render_template('checkout.html', form=form, cart_items=cart_items, total=total)


@main_bp.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    """Страница подтверждения заказа."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    return render_template('order_confirmation.html', order=order)


@main_bp.route('/add_to_cart_ajax/<int:product_id>', methods=['POST'])
def add_to_cart_ajax(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Товар не найден'}), 404

    if current_user.is_authenticated:
        # Ищем существующий элемент корзины
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
            db.session.add(cart_item)
        db.session.commit()
        cart_total = sum(item.quantity for item in CartItem.query.filter_by(user_id=current_user.id).all())
    else:
        # Гостевая корзина (сессия)
        cart = session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        session['cart'] = cart
        cart_total = sum(cart.values())

    return jsonify({
        'success': True,
        'product_name': product.name,
        'cart_total': cart_total
    })


@main_bp.route('/custom-order', methods=['GET', 'POST'])
def custom_order():
    form = CustomOrderForm()
    if form.validate_on_submit():

        if form.image.data:
            image_path = save_image(form.image.data)
        else:
            image_path = None

        custom_order = CustomOrder(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=form.name.data,
            contact=form.contact.data,
            product_type=form.product_type.data or None,
            description=form.description.data,
            image_path=image_path
        )
        db.session.add(custom_order)
        db.session.commit()
        flash('Ваша заявка отправлена! Мы свяжемся с вами в ближайшее время.', 'success')
        return redirect(url_for('main.home'))
    return render_template('custom_order.html', form=form)


@main_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Страница отдельного товара."""
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    return render_template('product_detail.html', product=product)
