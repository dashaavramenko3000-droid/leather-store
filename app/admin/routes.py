# app/admin/routes.py
"""
Маршруты админ-панели.
Включает управление товарами, заказами, заявками, отзывами,
настройками почты и журналом действий администратора.
"""
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, current_user

from . import admin_bp
from ..extensions import db, cache
from ..models import (
    User, Product, ProductImage, Order, OrderItem, CustomOrder,
    OrderStatusHistory, CustomOrderStatusHistory, OrderMessage,
    CustomOrderMessage, Review, EmailSettings, AdminLog, PromoCode, Setting
)
from ..forms import LoginForm, ProductForm, EmailSettingsForm, PromoCodeForm
from ..utils import save_image, delete_image_file


# ---------- Декоратор для проверки прав администратора ----------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


# ---------- Вспомогательная функция для логирования ----------
def log_action(action, details=None):
    """Записывает действие администратора в журнал."""
    if current_user.is_authenticated and current_user.is_admin:
        log = AdminLog(admin_id=current_user.id, action=action, details=details)
        db.session.add(log)
        db.session.commit()


# ---------- Аутентификация ----------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Вы успешно вошли', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Неверный логин или пароль', 'danger')
    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout')
@admin_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('admin.login'))


# ---------- Главная страница админки ----------
@admin_bp.route('/')
@admin_required
def dashboard():
    product_count = Product.query.count()
    order_count = Order.query.count()
    custom_orders_count = CustomOrder.query.count()
    completed_orders_total = (
            Order.query.filter_by(status='completed').count() +
            CustomOrder.query.filter_by(status='completed').count()
    )
    return render_template(
        'admin/dashboard.html',
        product_count=product_count,
        order_count=order_count,
        custom_orders_count=custom_orders_count,
        completed_orders_total=completed_orders_total
    )


# ---------- Управление товарами ----------
@admin_bp.route('/products')
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    pagination = query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        'admin/products.html',
        products=pagination.items,
        search=search,
        pagination=pagination
    )


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            product_type=form.product_type.data,
            description=form.description.data,
            price=form.price.data,
            material=form.material.data,
            color=form.color.data,
            dimensions=form.dimensions.data,
            weight=form.weight.data
        )
        db.session.add(product)
        db.session.flush()  # получить id

        # Сохраняем изображения
        if form.images.data:
            for i, file in enumerate(form.images.data):
                if file.filename:
                    path = save_image(file)
                    if path:
                        img = ProductImage(product_id=product.id, image_path=path, order=i)
                        db.session.add(img)

        db.session.commit()
        cache.clear()  # инвалидация кэша каталога
        log_action('Добавил товар', f'ID: {product.id}, Название: {product.name}')
        flash('Товар добавлен', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', form=form, title='Добавить товар', product=None)


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.product_type = form.product_type.data
        product.description = form.description.data
        product.price = form.price.data
        product.material = form.material.data
        product.color = form.color.data
        product.dimensions = form.dimensions.data
        product.weight = form.weight.data

        # Добавление новых изображений
        if form.images.data:
            max_order = max([img.order for img in product.images], default=-1)
            for i, file in enumerate(form.images.data):
                if file.filename:
                    path = save_image(file)
                    if path:
                        img = ProductImage(product_id=product.id, image_path=path, order=max_order + 1 + i)
                        db.session.add(img)

        # Удаление отмеченных изображений
        delete_ids = request.form.getlist('delete_images')
        if delete_ids:
            for img_id in delete_ids:
                img = db.session.get(ProductImage, int(img_id))
                if img and img.product_id == product.id:
                    delete_image_file(img.image_path)
                    db.session.delete(img)

        db.session.commit()
        cache.clear()
        log_action('Изменил товар', f'ID: {product.id}, Название: {product.name}')
        flash('Товар обновлён', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', form=form, title='Редактировать товар', product=product)


@admin_bp.route('/products/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    # Удаляем файлы изображений
    for img in product.images:
        delete_image_file(img.image_path)

    db.session.delete(product)
    db.session.commit()
    cache.clear()
    log_action('Удалил товар', f'ID: {product.id}, Название: {product.name}')
    flash('Товар удалён', 'success')
    return redirect(url_for('admin.products'))


# ---------- Заказы ----------
@admin_bp.route('/orders')
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Фильтры
    filter_id = request.args.get('id', type=int)
    filter_status = request.args.get('status', '')
    filter_date = request.args.get('date', '')

    query = Order.query
    if filter_id:
        query = query.filter(Order.id == filter_id)
    if filter_status:
        query = query.filter(Order.status == filter_status)
    if filter_date:
        try:
            date_obj = datetime.strptime(filter_date, '%Y-%m-%d')
            next_day = date_obj + timedelta(days=1)
            query = query.filter(Order.created_at >= date_obj, Order.created_at < next_day)
        except ValueError:
            pass

    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        'admin/orders.html',
        orders=pagination.items,
        pagination=pagination,
        filter_id=filter_id,
        filter_status=filter_status,
        filter_date=filter_date
    )


@admin_bp.route('/orders/<int:order_id>', methods=['GET', 'POST'])
@admin_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            msg = OrderMessage(
                order_id=order.id,
                sender_type='admin',
                message=message
            )
            db.session.add(msg)
            db.session.commit()
            flash('Сообщение отправлено', 'success')
            return redirect(url_for('admin.order_detail', order_id=order.id))

    return render_template('admin/order_detail.html', order=order)


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    new_status = request.form.get('status')
    allowed_statuses = ['new', 'processing', 'shipped', 'completed', 'cancelled']
    if new_status not in allowed_statuses:
        flash('Недопустимый статус', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order.id))

    old_status = order.status
    order.status = new_status
    # История статусов
    history = OrderStatusHistory(order_id=order.id, status=new_status)
    db.session.add(history)
    db.session.commit()

    log_action('Изменил статус заказа', f'Заказ #{order.id}: {old_status} -> {new_status}')
    flash('Статус заказа обновлён', 'success')
    return redirect(url_for('admin.order_detail', order_id=order.id))


@admin_bp.route('/orders/delete/<int:order_id>')
@admin_required
def delete_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    db.session.delete(order)
    db.session.commit()
    log_action('Удалил заказ', f'Заказ #{order.id}')
    flash('Заказ удалён', 'success')
    return redirect(url_for('admin.orders'))


# ---------- Индивидуальные заявки ----------
@admin_bp.route('/custom-orders')
@admin_required
def custom_orders():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    filter_id = request.args.get('id', type=int)
    filter_status = request.args.get('status', '')
    filter_date = request.args.get('date', '')

    query = CustomOrder.query
    if filter_id:
        query = query.filter(CustomOrder.id == filter_id)
    if filter_status:
        query = query.filter(CustomOrder.status == filter_status)
    if filter_date:
        try:
            date_obj = datetime.strptime(filter_date, '%Y-%m-%d')
            next_day = date_obj + timedelta(days=1)
            query = query.filter(CustomOrder.created_at >= date_obj, CustomOrder.created_at < next_day)
        except ValueError:
            pass

    pagination = query.order_by(CustomOrder.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        'admin/custom_orders.html',
        requests=pagination.items,
        pagination=pagination,
        filter_id=filter_id,
        filter_status=filter_status,
        filter_date=filter_date
    )


@admin_bp.route('/custom-orders/<int:order_id>', methods=['GET', 'POST'])
@admin_required
def custom_order_detail(order_id):
    custom_order = db.session.get(CustomOrder, order_id)
    if not custom_order:
        abort(404)

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            msg = CustomOrderMessage(
                custom_order_id=custom_order.id,
                sender_type='admin',
                message=message
            )
            db.session.add(msg)
            db.session.commit()
            flash('Сообщение отправлено', 'success')
            return redirect(url_for('admin.custom_order_detail', order_id=custom_order.id))

    return render_template('admin/custom_order_detail.html', custom_order=custom_order)


@admin_bp.route('/custom-orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_custom_order_status(order_id):
    custom_order = db.session.get(CustomOrder, order_id)
    if not custom_order:
        abort(404)

    new_status = request.form.get('status')
    allowed_statuses = ['new', 'in_progress', 'completed', 'cancelled']
    if new_status not in allowed_statuses:
        flash('Недопустимый статус', 'danger')
        return redirect(url_for('admin.custom_order_detail', order_id=custom_order.id))

    old_status = custom_order.status
    custom_order.status = new_status
    history = CustomOrderStatusHistory(custom_order_id=custom_order.id, status=new_status)
    db.session.add(history)
    db.session.commit()

    log_action('Изменил статус заявки', f'Заявка #{custom_order.id}: {old_status} -> {new_status}')
    flash('Статус заявки обновлён', 'success')
    return redirect(url_for('admin.custom_order_detail', order_id=custom_order.id))


@admin_bp.route('/custom-orders/delete/<int:order_id>')
@admin_required
def delete_custom_order(order_id):
    custom_order = db.session.get(CustomOrder, order_id)
    if not custom_order:
        abort(404)

    db.session.delete(custom_order)
    db.session.commit()
    log_action('Удалил заявку', f'Заявка #{custom_order.id}')
    flash('Заявка удалена', 'success')
    return redirect(url_for('admin.custom_orders'))


# ---------- Отзывы ----------
@admin_bp.route('/reviews')
@admin_required
def reviews():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = Review.query.order_by(Review.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/reviews.html', reviews=pagination.items, pagination=pagination)


@admin_bp.route('/reviews/<int:review_id>/approve')
@admin_required
def approve_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        abort(404)
    review.is_approved = True
    db.session.commit()
    log_action('Одобрил отзыв', f'Отзыв #{review.id}')
    flash('Отзыв одобрен', 'success')
    return redirect(url_for('admin.reviews'))


@admin_bp.route('/reviews/<int:review_id>/disapprove')
@admin_required
def disapprove_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        abort(404)
    review.is_approved = False
    db.session.commit()
    log_action('Снял отзыв с публикации', f'Отзыв #{review.id}')
    flash('Отзыв снят с публикации', 'warning')
    return redirect(url_for('admin.reviews'))


@admin_bp.route('/reviews/<int:review_id>/delete')
@admin_required
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        abort(404)
    db.session.delete(review)
    db.session.commit()
    log_action('Удалил отзыв', f'Отзыв #{review.id}')
    flash('Отзыв удалён', 'success')
    return redirect(url_for('admin.reviews'))


# ---------- Настройки почты ----------
@admin_bp.route('/email-settings', methods=['GET', 'POST'])
@admin_required
def email_settings():
    settings = db.session.get(EmailSettings, 1)
    if not settings:
        settings = EmailSettings(id=1)
        db.session.add(settings)
        db.session.commit()

    form = EmailSettingsForm(obj=settings)
    if form.validate_on_submit():
        settings.mail_server = form.mail_server.data
        settings.mail_port = form.mail_port.data
        settings.mail_use_ssl = form.mail_use_ssl.data
        settings.mail_use_tls = form.mail_use_tls.data
        settings.mail_username = form.mail_username.data
        settings.mail_password = form.mail_password.data
        settings.mail_default_sender = form.mail_default_sender.data
        settings.admin_email = form.admin_email.data
        db.session.commit()

        # Применяем настройки к текущему приложению
        current_app.config.update(
            MAIL_SERVER=settings.mail_server,
            MAIL_PORT=settings.mail_port,
            MAIL_USE_SSL=settings.mail_use_ssl,
            MAIL_USE_TLS=settings.mail_use_tls,
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_DEFAULT_SENDER=settings.mail_default_sender,
            ADMIN_EMAIL=settings.admin_email
        )
        # Переинициализируем mail, чтобы применились новые параметры
        from ..extensions import mail
        mail.init_app(current_app)
        log_action('Обновил настройки почты', '')
        flash('Настройки почты сохранены', 'success')
        return redirect(url_for('admin.email_settings'))

    return render_template('admin/email_settings.html', form=form)


# ---------- Журнал действий ----------
@admin_bp.route('/logs')
@admin_required
def admin_logs():
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(100).all()
    return render_template('admin/logs.html', logs=logs)


@admin_bp.route('/promo-codes')
@admin_required
def promo_codes():
    codes = PromoCode.query.order_by(PromoCode.valid_until.desc()).all()
    return render_template('admin/promo_codes.html', codes=codes)


@admin_bp.route('/promo-codes/add', methods=['GET', 'POST'])
@admin_required
def add_promo_code():
    form = PromoCodeForm()
    if form.validate_on_submit():
        code = PromoCode(
            code=form.code.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            valid_from=form.valid_from.data,
            valid_until=form.valid_until.data,
            usage_limit=form.usage_limit.data,
            active=form.active.data
        )
        db.session.add(code)
        db.session.commit()
        flash('Промокод добавлен', 'success')
        return redirect(url_for('admin.promo_codes'))
    return render_template('admin/promo_code_form.html', form=form, title='Добавить промокод')


@admin_bp.route('/promo-codes/edit/<int:code_id>', methods=['GET', 'POST'])
@admin_required
def edit_promo_code(code_id):
    code = db.session.get(PromoCode, code_id)
    if not code:
        abort(404)
    form = PromoCodeForm(obj=code)
    if form.validate_on_submit():
        code.code = form.code.data
        code.discount_type = form.discount_type.data
        code.discount_value = form.discount_value.data
        code.valid_from = form.valid_from.data
        code.valid_until = form.valid_until.data
        code.usage_limit = form.usage_limit.data
        code.active = form.active.data
        db.session.commit()
        flash('Промокод обновлён', 'success')
        return redirect(url_for('admin.promo_codes'))
    return render_template('admin/promo_code_form.html', form=form, title='Редактировать промокод', promo_code=code)


@admin_bp.route('/promo-codes/delete/<int:code_id>')
@admin_required
def delete_promo_code(code_id):
    code = db.session.get(PromoCode, code_id)
    if not code:
        abort(404)
    db.session.delete(code)
    db.session.commit()
    flash('Промокод удалён', 'success')
    return redirect(url_for('admin.promo_codes'))


@admin_bp.route('/site-settings', methods=['GET', 'POST'])
@admin_required
def site_settings():
    show_promo = Setting.query.filter_by(key='show_promo_code_field').first()
    if not show_promo:
        show_promo = Setting(key='show_promo_code_field', value='true')
        db.session.add(show_promo)
        db.session.commit()

    if request.method == 'POST':
        show_promo.value = 'true' if request.form.get('show_promo_code_field') == 'on' else 'false'
        db.session.commit()
        flash('Настройки сохранены', 'success')
        return redirect(url_for('admin.site_settings'))

    return render_template('admin/site_settings.html', show_promo=show_promo.value)
