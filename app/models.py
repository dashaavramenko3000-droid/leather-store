from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    """Пользователь (администратор)."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    """Товар (изделие из кожи)."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)  # Цена в рублях
    product_type = db.Column(db.String(50), nullable=False, default='Кошелёк')
    images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan', order_by='ProductImage.order')

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductImage(db.Model):
    """Фотографии товара."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<ProductImage {self.image_path}>'


class Order(db.Model):
    """Заказ клиента."""
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(50), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    comment = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Integer, nullable=False)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id}>'


class OrderItem(db.Model):
    """Позиция в заказе."""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='SET NULL'), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)  # Название на момент покупки
    price = db.Column(db.Integer, nullable=False)  # Цена за единицу
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f'<OrderItem {self.id}>'