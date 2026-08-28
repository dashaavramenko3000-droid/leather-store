from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, current_user
from . import admin_bp
from ..forms import LoginForm, ProductForm
from ..utils import save_image, delete_image_file
from ..models import db, Product, ProductImage, User, Order, CustomOrder, OrderStatusHistory, CustomOrderStatusHistory


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
            price=form.price.data
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


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
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


@admin_bp.route('/custom-orders/<int:order_id>')
@admin_required
def custom_order_detail(order_id):
    """Просмотр деталей индивидуального заказа."""
    custom_order = db.session.get(CustomOrder, order_id)
    if not custom_order:
        abort(404)
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
