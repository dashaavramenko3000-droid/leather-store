import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from PIL import Image
from werkzeug.utils import secure_filename
from models import db, Product, ProductImage, User
from forms import LoginForm, ProductForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def save_image(file):
    """Сохраняет одно изображение, сжимает и возвращает относительный путь."""
    if file and file.filename:
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
        img = Image.open(file)
        img.thumbnail((1200, 1200))
        img.save(file_path, optimize=True, quality=85)
        return 'uploads/' + unique_name
    return None


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
    return render_template('admin/dashboard.html', product_count=product_count)


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

        # Сохраняем загруженные изображения
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
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.product_type = form.product_type.data
        product.description = form.description.data
        product.price = form.price.data

        # Добавление новых изображений
        if form.images.data:
            # Определяем следующий порядок
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
                img = ProductImage.query.get(int(img_id))
                if img and img.product_id == product.id:
                    # Удаляем файл
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                             img.image_path.replace('uploads/', '', 1))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    db.session.delete(img)

        db.session.commit()
        flash('Товар обновлён', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', form=form, title='Редактировать товар', product=product)


@admin_bp.route('/products/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Удаляем файлы всех изображений
    for img in product.images:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], img.image_path.replace('uploads/', '', 1))
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(product)  # благодаря cascade удалит и записи в ProductImage
    db.session.commit()
    flash('Товар удалён', 'success')
    return redirect(url_for('admin.products'))
