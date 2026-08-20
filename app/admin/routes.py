import os
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import admin_bp
from ..extensions import db
from ..models import User, Product, ProductImage, Order
from ..forms import LoginForm, ProductForm
from ..utils import save_image, delete_image_file


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
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@login_required
def dashboard():
    product_count = Product.query.count()
    order_count = Order.query.count()
    return render_template('admin/dashboard.html', product_count=product_count, order_count=order_count)


@admin_bp.route('/products')
@login_required
def products():
    search = request.args.get('search', '')
    if search:
        products_list = Product.query.filter(Product.name.ilike(f'%{search}%')).all()
    else:
        products_list = Product.query.all()
    return render_template('admin/products.html', products=products_list, search=search)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
def orders():
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=all_orders)


@admin_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    return render_template('admin/order_detail.html', order=order)


@admin_bp.route('/orders/delete/<int:order_id>')
@login_required
def delete_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    db.session.delete(order)
    db.session.commit()
    flash('Заказ удалён', 'success')
    return redirect(url_for('admin.orders'))