from datetime import datetime, timedelta
from functools import wraps, cache
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, current_user

from app import mail
from ..email_utils import send_email
from . import admin_bp
from ..forms import LoginForm, ProductForm, EmailSettingsForm
from ..utils import save_image, delete_image_file
from ..models import db, Product, ProductImage, User, Order, CustomOrder, OrderStatusHistory, CustomOrderStatusHistory, \
    OrderMessage, CustomOrderMessage, Review, EmailSettings


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


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


@admin_bp.route('/')
@admin_required
def dashboard():
    product_count = Product.query.count()
    order_count = Order.query.count()
    custom_orders_count = CustomOrder.query.count()  # количество индивидуальных заявок
    completed_orders_total = (
            Order.query.filter_by(status='completed').count() +
            CustomOrder.query.filter_by(status='completed').count()
    )  # выполненные заказы всех типов

    return render_template(
        'admin/dashboard.html',
        product_count=product_count,
        order_count=order_count,
        custom_orders_count=custom_orders_count,
        completed_orders_total=completed_orders_total,
    )


@admin_bp.route('/products')
@admin_required
def products():
    search = request.args.get('search', '')
    if search:
        products_list = Product.query.filter(Product.name.ilike(f'%{search}%')).all()
    else:
        products_list = Product.query.all()
    return render_template('admin/products.html', products=products_list, search=search)


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
        cache.clear()
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
        product.material = form.material.data,
        product.color = form.color.data,
        product.dimensions = form.dimensions.data,
        product.weight = form.weight.data
        product.description = form.description.data
        product.price = form.price.data

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
    flash('Товар удалён', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/orders')
@admin_required
def orders():
    # Получение параметров фильтрации
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
            pass  # некорректная дата игнорируется

    all_orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html',
                           orders=all_orders,
                           filter_id=filter_id,
                           filter_status=filter_status,
                           filter_date=filter_date)


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


@admin_bp.route('/orders/delete/<int:order_id>')
@admin_required
def delete_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    db.session.delete(order)
    db.session.commit()
    flash('Заказ удалён', 'success')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/custom-orders')
@admin_required
def custom_orders():
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

    requests = query.order_by(CustomOrder.created_at.desc()).all()
    return render_template('admin/custom_orders.html',
                           requests=requests,
                           filter_id=filter_id,
                           filter_status=filter_status,
                           filter_date=filter_date)


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


@admin_bp.route('/custom-orders/delete/<int:order_id>')
@admin_required
def delete_custom_order(order_id):
    custom_order = db.session.get(CustomOrder, order_id)
    if not custom_order:
        abort(404)
    db.session.delete(custom_order)
    db.session.commit()
    flash('Заявка удалена', 'success')
    return redirect(url_for('admin.custom_orders'))


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

    # Обновляем текущий статус
    order.status = new_status
    # Добавляем запись в историю
    history = OrderStatusHistory(order_id=order.id, status=new_status)
    db.session.add(history)
    db.session.commit()
    if order.customer_email:
        send_email(
            f'Статус заказа #{order.id} изменён',
            [order.customer_email],
            'email/order_status.html',
            order=order
        )

    flash('Статус заказа обновлён', 'success')
    return redirect(url_for('admin.order_detail', order_id=order.id))


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

    custom_order.status = new_status
    history = CustomOrderStatusHistory(custom_order_id=custom_order.id, status=new_status)
    db.session.add(history)
    db.session.commit()

    flash('Статус заявки обновлён', 'success')
    return redirect(url_for('admin.custom_order_detail', order_id=custom_order.id))


@admin_bp.route('/reviews')
@admin_required
def reviews():
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=all_reviews)


@admin_bp.route('/reviews/<int:review_id>/approve')
@admin_required
def approve_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        abort(404)
    review.is_approved = True
    db.session.commit()
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
    flash('Отзыв удалён', 'success')
    return redirect(url_for('admin.reviews'))


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
        mail.init_app(current_app)
        flash('Настройки почты сохранены', 'success')
        return redirect(url_for('admin.email_settings'))

    return render_template('admin/email_settings.html', form=form)