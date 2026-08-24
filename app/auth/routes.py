from flask import render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from ..extensions import db
from ..models import User, Order, WishlistItem, Product, CartItem
from ..forms import CustomerLoginForm, RegistrationForm, UpdateProfileForm


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('auth/register.html', form=form)

        user = User(
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            address=form.address.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Автоматический вход после регистрации
        login_user(user)
        flash('Регистрация успешна! Вы вошли в свой аккаунт.', 'success')
        return redirect(url_for('auth.account'))   # или url_for('main.home')
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = CustomerLoginForm()
    if form.validate_on_submit():
        # Ищем по email или username
        user = User.query.filter(
            (User.email == form.email_or_username.data) | (User.username == form.email_or_username.data)
        ).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            guest_cart = session.get('cart', {})
            if guest_cart:
                for product_id, qty in guest_cart.items():
                    product = db.session.get(Product, int(product_id))
                    if product:
                        existing_item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
                        if existing_item:
                            existing_item.quantity += qty
                        else:
                            new_item = CartItem(user_id=user.id, product_id=product_id, quantity=qty)
                            db.session.add(new_item)
                session.pop('cart', None)  # очищаем гостевую корзину
                db.session.commit()
            flash('Вы вошли', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.home'))
        flash('Неверный email/логин или пароль', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/account')
@login_required
def account():
    return render_template('auth/account.html', user=current_user)


@auth_bp.route('/account/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('auth/orders.html', orders=user_orders)


@auth_bp.route('/account/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('auth/order_detail.html', order=order)


@auth_bp.route('/account/profile', methods=['GET', 'POST'])
@login_required
def profile():
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
    items = WishlistItem.query.filter_by(user_id=current_user.id).order_by(WishlistItem.created_at.desc()).all()
    products = [item.product for item in items]
    return render_template('auth/wishlist.html', products=products)


@auth_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
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
    item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Товар удалён из избранного', 'success')
    return redirect(request.referrer or url_for('auth.wishlist'))
