from flask import render_template, request, session, redirect, url_for, flash, jsonify, abort
from flask_login import current_user

from . import main_bp
from ..extensions import db
from ..models import Product, Order, OrderItem
from ..forms import CheckoutForm


@main_bp.context_processor
def inject_cart_total():
    """Добавляет общее количество товаров в корзине во все шаблоны."""
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
    """Добавление товара в корзину (использует сессию)."""
    product = db.session.get(Product, product_id)
    if not product:
        flash('Товар не найден', 'danger')
        return redirect(url_for('main.catalog'))

    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f'Товар "{product.name}" добавлен в корзину', 'success')
    return redirect(request.referrer or url_for('main.catalog'))


@main_bp.route('/cart')
def cart():
    """Страница корзины."""
    cart = session.get('cart', {})
    # Убираем товары, которых уже нет в базе
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


@main_bp.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Обновление количества товара (обычный POST)."""
    cart = session.get('cart', {})
    qty = int(request.form.get('quantity', 1))
    if qty <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = qty
    session['cart'] = cart
    return redirect(url_for('main.cart'))


@main_bp.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    """Удаление товара из корзины (обычный запрос)."""
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('main.cart'))


@main_bp.route('/cart/update_ajax/<int:product_id>', methods=['POST'])
def update_cart_ajax(product_id):
    """AJAX-обновление количества товара."""
    cart = session.get('cart', {})
    try:
        qty = int(request.form.get('quantity', 1))
    except ValueError:
        return jsonify({'success': False, 'message': 'Некорректное количество'}), 400

    if qty <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = qty
    session['cart'] = cart

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Товар не найден'}), 404

    subtotal = product.price * qty
    total = 0
    for pid, quantity in cart.items():
        p = db.session.get(Product, int(pid))
        if p:
            total += p.price * quantity

    cart_total = sum(cart.values())
    return jsonify({
        'success': True,
        'quantity': qty,
        'subtotal': subtotal,
        'total': total,
        'cart_total': cart_total
    })


@main_bp.route('/cart/remove_ajax/<int:product_id>', methods=['POST'])
def remove_from_cart_ajax(product_id):
    """AJAX-удаление товара из корзины."""
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
    """Оформление заказа."""
    cart = session.get('cart', {})
    if not cart:
        flash('Ваша корзина пуста', 'info')
        return redirect(url_for('main.catalog'))

    # Очистка корзины от удалённых товаров
    updated_cart = dict(cart)
    removed_products = []
    for product_id in list(updated_cart.keys()):
        product = db.session.get(Product, int(product_id))
        if not product:
            updated_cart.pop(product_id, None)
            removed_products.append(product_id)

    if removed_products:
        session['cart'] = updated_cart
        cart = updated_cart
        if len(removed_products) == 1:
            flash('Один из товаров был удалён из каталога и убран из вашей корзины.', 'warning')
        else:
            flash(
                f'Несколько товаров были удалены из каталога и убраны из вашей корзины ({len(removed_products)} шт.).',
                'warning')
        if not cart:
            flash('Все товары из вашей корзины были удалены.', 'info')
            return redirect(url_for('main.catalog'))

    form = CheckoutForm()
    if form.validate_on_submit():
        total = 0
        items_data = []
        for product_id, qty in cart.items():
            product = db.session.get(Product, int(product_id))
            if product:
                subtotal = product.price * qty
                total += subtotal
                items_data.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

        if not items_data:
            session.pop('cart', None)
            flash('К сожалению, все товары в корзине недоступны. Заказ не оформлен.', 'danger')
            return redirect(url_for('main.catalog'))

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
        session.pop('cart', None)
        flash('Заказ успешно оформлен! Мы свяжемся с вами.', 'success')
        return redirect(url_for('main.order_confirmation', order_id=order.id))

    # GET-запрос или ошибки валидации
    cart_items = []
    total = 0
    for product_id, qty in cart.items():
        product = db.session.get(Product, int(product_id))
        if product:
            subtotal = product.price * qty
            total += subtotal
            cart_items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

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

    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart

    # Общее количество товаров в корзине (сумма всех единиц)
    cart_total = sum(cart.values())

    return jsonify({
        'success': True,
        'product_name': product.name,
        'cart_total': cart_total
    })
