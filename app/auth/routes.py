# app/auth/routes.py
"""
Маршруты аутентификации и личного кабинета покупателя.
Включает: регистрацию, вход/выход, профиль, историю заказов, избранное, сброс пароля.
"""
from email.headerregistry import Address
from uuid import uuid4
from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user

from ..email_utils import send_email
from . import auth_bp
from ..extensions import db
from ..models import User, Order, WishlistItem, Product, CartItem, CustomOrder, OrderMessage, CustomOrderMessage, \
    Address
from ..forms import (
    CustomerLoginForm,
    RegistrationForm,
    UpdateProfileForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
    ChangePasswordForm, AddressForm
)


def link_guest_orders_to_user(user):
    """
    Привязывает гостевые заказы и индивидуальные заявки к аккаунту,
    если email совпадает с указанным при оформлении.
    """
    orders_updated = Order.query.filter_by(user_id=None, customer_email=user.email).update({'user_id': user.id})
    custom_orders_updated = CustomOrder.query.filter_by(user_id=None, contact=user.email).update({'user_id': user.id})
    db.session.commit()
    return orders_updated, custom_orders_updated


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Регистрация нового покупателя.
    После успешной регистрации пользователь автоматически входит в систему
    и перенаправляется в личный кабинет.
    """
    # Если пользователь уже авторизован, отправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Проверяем, не занят ли email
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('auth/register.html', form=form)

        # Создаём нового пользователя
        user = User(
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            address=form.address.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Привязываем гостевые заказы и заявки
        orders_linked, custom_linked = link_guest_orders_to_user(user)
        if orders_linked or custom_linked:
            flash('Мы нашли ваши предыдущие заказы и привязали их к аккаунту.', 'info')

        send_email(
            'Добро пожаловать в Кожаную мастерскую!',
            [user.email],
            'email/register.html',
            user=user
        )

        # Автоматический вход после регистрации
        login_user(user)
        flash('Регистрация успешна! Вы вошли в свой аккаунт.', 'success')
        return redirect(url_for('auth.account'))  # или url_for('main.home')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Вход для покупателей по email или логину.
    Если у пользователя была гостевая корзина, она переносится в его аккаунт.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = CustomerLoginForm()
    if form.validate_on_submit():
        # Поиск пользователя по email или username
        user = User.query.filter(
            (User.email == form.email_or_username.data) |
            (User.username == form.email_or_username.data)
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            if user.email:
                orders_linked, custom_linked = link_guest_orders_to_user(user)
                if orders_linked or custom_linked:
                    flash('Ваши предыдущие заказы были привязаны к аккаунту.', 'info')

            # Переносим гостевую корзину (из сессии) в корзину пользователя (БД)
            guest_cart = session.get('cart', {})
            if guest_cart:
                for product_id, qty in guest_cart.items():
                    product = db.session.get(Product, int(product_id))
                    if product:
                        existing_item = CartItem.query.filter_by(
                            user_id=user.id, product_id=product_id
                        ).first()
                        if existing_item:
                            existing_item.quantity += qty
                        else:
                            new_item = CartItem(user_id=user.id, product_id=product_id, quantity=qty)
                            db.session.add(new_item)
                session.pop('cart', None)  # очищаем гостевую корзину
                db.session.commit()

            flash('Вы вошли', 'success')

            # Обработка next для перенаправления (защита от открытого редиректа)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.home'))

        flash('Неверный email/логин или пароль', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из аккаунта."""
    logout_user()
    flash('Вы вышли', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/account')
@login_required
def account():
    """Личный кабинет пользователя (профиль и ссылки)."""
    return render_template('auth/account.html', user=current_user)


@auth_bp.route('/account/addresses')
@login_required
def addresses():
    user_addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.is_default.desc()).all()
    return render_template('auth/addresses.html', addresses=user_addresses)


@auth_bp.route('/account/addresses/add', methods=['GET', 'POST'])
@login_required
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        # Если это первый адрес или отмечен как основной, сбрасываем is_default у остальных
        if form.is_default.data or not Address.query.filter_by(user_id=current_user.id).first():
            # сбрасываем все
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
            is_default = True
        else:
            is_default = False

        address = Address(
            user_id=current_user.id,
            address_line=form.address_line.data,
            city=form.city.data,
            postal_code=form.postal_code.data,
            is_default=is_default
        )
        db.session.add(address)
        db.session.commit()
        flash('Адрес добавлен', 'success')
        return redirect(url_for('auth.addresses'))
    return render_template('auth/address_form.html', form=form, title='Добавить адрес')


@auth_bp.route('/account/addresses/edit/<int:address_id>', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    address = db.session.get(Address, address_id)
    if not address or address.user_id != current_user.id:
        abort(404)

    form = AddressForm(obj=address)
    if form.validate_on_submit():
        if form.is_default.data:
            # сбрасываем is_default у всех других адресов
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
        address.address_line = form.address_line.data
        address.city = form.city.data
        address.postal_code = form.postal_code.data
        address.is_default = form.is_default.data
        db.session.commit()
        flash('Адрес обновлён', 'success')
        return redirect(url_for('auth.addresses'))
    return render_template('auth/address_form.html', form=form, title='Редактировать адрес')


@auth_bp.route('/account/addresses/delete/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    address = db.session.get(Address, address_id)
    if not address or address.user_id != current_user.id:
        abort(404)
    db.session.delete(address)
    db.session.commit()
    flash('Адрес удалён', 'success')
    return redirect(url_for('auth.addresses'))


@auth_bp.route('/account/addresses/set-default/<int:address_id>', methods=['POST'])
@login_required
def set_default_address(address_id):
    address = db.session.get(Address, address_id)
    if not address or address.user_id != current_user.id:
        abort(404)
    # сбрасываем все is_default
    Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
    address.is_default = True
    db.session.commit()
    flash('Основной адрес изменён', 'success')
    return redirect(url_for('auth.addresses'))


@auth_bp.route('/account/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Обычные заказы
    user_orders = Order.query.filter_by(user_id=current_user.id) \
        .order_by(Order.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)
    # Индивидуальные заказы
    custom_orders = CustomOrder.query.filter_by(user_id=current_user.id) \
        .order_by(CustomOrder.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('auth/orders.html',
                           orders=user_orders.items,
                           custom_orders=custom_orders.items,
                           orders_pagination=user_orders,
                           custom_orders_pagination=custom_orders)


@auth_bp.route('/account/custom-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def custom_order_detail(order_id):
    custom_order = db.session.get(CustomOrder, order_id)
    if not custom_order or custom_order.user_id != current_user.id:
        abort(404)

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            msg = CustomOrderMessage(
                custom_order_id=custom_order.id,
                sender_type='customer',
                message=message
            )
            db.session.add(msg)
            db.session.commit()
            flash('Сообщение отправлено', 'success')
            return redirect(url_for('auth.custom_order_detail', order_id=custom_order.id))

    return render_template('auth/custom_order_detail.html', custom_order=custom_order)


@auth_bp.route('/account/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Текущий пароль указан неверно', 'danger')
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Пароль успешно изменён', 'success')
        return redirect(url_for('auth.account'))

    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/account/orders/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        abort(404)

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            msg = OrderMessage(
                order_id=order.id,
                sender_type='customer',
                message=message
            )
            db.session.add(msg)
            db.session.commit()
            flash('Сообщение отправлено', 'success')
            return redirect(url_for('auth.order_detail', order_id=order.id))

    return render_template('auth/order_detail.html', order=order)


@auth_bp.route('/account/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Редактирование профиля пользователя."""
    form = UpdateProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        db.session.commit()
        flash('Профиль обновлён', 'success')
        return redirect(url_for('auth.account'))
    return render_template('auth/profile.html', form=form)


@auth_bp.route('/wishlist')
@login_required
def wishlist():
    page = request.args.get('page', 1, type=int)
    per_page = 12

    pagination = WishlistItem.query.filter_by(user_id=current_user.id) \
        .order_by(WishlistItem.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    items = pagination.items
    products = [item.product for item in items]

    return render_template('auth/wishlist.html',
                           products=products,
                           pagination=pagination)


@auth_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Добавление товара в избранное."""
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    existing = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash('Товар уже в избранном', 'info')
    else:
        item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
        flash('Товар добавлен в избранное', 'success')

    return redirect(request.referrer or url_for('main.catalog'))


@auth_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    """Удаление товара из избранного."""
    item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Товар удалён из избранного', 'success')
    return redirect(request.referrer or url_for('auth.wishlist'))


@auth_bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Шаг 1: запрос на сброс пароля.
    Генерирует токен, сохраняет его в БД и (в перспективе) отправляет письмо.
    """
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = str(uuid4())
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            # В реальном приложении здесь будет отправка письма через Flask-Mail
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_email(
                'Восстановление пароля',
                [user.email],
                'email/reset_password.html',
                reset_url=reset_url
            )
            flash('Инструкция отправлена на ваш email.', 'info')
        else:
            # Не раскрываем, существует ли email, чтобы избежать перебора
            flash('Если такой email зарегистрирован, на него отправлено письмо.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_request.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Шаг 2: установка нового пароля по уникальному токену.
    Токен действителен в течение 1 часа.
    """
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('Ссылка недействительна или срок её действия истёк.', 'danger')
        return redirect(url_for('auth.reset_password_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        flash('Пароль успешно изменён. Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)
