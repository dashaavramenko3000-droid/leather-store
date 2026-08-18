import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from PIL import Image
from werkzeug.utils import secure_filename
from models import db, Product, User
from forms import LoginForm, ProductForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def save_image(file):
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
        image_path = save_image(form.image.data)
        product = Product(
            name=form.name.data,
            product_type=form.product_type.data,
            description=form.description.data,
            price=form.price.data,
            image=image_path if image_path else ''
        )
        db.session.add(product)
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
        if form.image.data:
            # Удаляем старое изображение, если оно было загружено ранее
            if product.image and not product.image.startswith('http'):
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], product.image.replace('uploads/', '', 1))
                if os.path.exists(old_path):
                    os.remove(old_path)
            product.image = save_image(form.image.data)
        db.session.commit()
        flash('Товар обновлён', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', form=form, title='Редактировать товар', product=product)

@admin_bp.route('/products/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Удаляем файл изображения, если он был загружен
    if product.image and not product.image.startswith('http'):
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], product.image.replace('uploads/', '', 1))
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(product)
    db.session.commit()
    flash('Товар удалён', 'success')
    return redirect(url_for('admin.products'))