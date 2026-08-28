from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)  # для админа, может быть NULL
    email = db.Column(db.String(120), unique=True, nullable=True)  # для покупателей
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='customer', lazy=True)
    wishlist_items = db.relationship('WishlistItem', backref='user', lazy=True, cascade='all, delete-orphan')
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email or self.username}>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    product_type = db.Column(db.String(50), nullable=False, default='Кошелёк')

    images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan',
                             order_by='ProductImage.order')

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<ProductImage {self.image_path}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # NULL, если гость
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    address = db.Column(db.Text)
    comment = db.Column(db.Text)
    status = db.Column(db.String(20), default='new')  # new, processing, shipped, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Integer, nullable=False)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', back_populates='order', cascade='all, delete-orphan',
                                     order_by='OrderStatusHistory.changed_at')
    messages = db.relationship('OrderMessage', back_populates='order', cascade='all, delete-orphan',
                               order_by='OrderMessage.created_at')

    def __repr__(self):
        return f'<Order {self.id}>'


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='SET NULL'), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', backref='order_items')


class OrderMessage(db.Model):
    """Сообщение в чате обычного заказа."""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'admin' или 'customer'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', back_populates='messages')

    def __repr__(self):
        return f'<OrderMessage {self.id}>'


class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='wishlist_items')


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

    def __repr__(self):
        return f'<CartItem {self.id}>'


class CustomOrder(db.Model):
    """Заявка на индивидуальный заказ."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # если авторизован
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)  # email или телефон
    product_type = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='custom_orders')
    status = db.Column(db.String(20), nullable=False, default='new')
    status_history = db.relationship('CustomOrderStatusHistory', back_populates='custom_order',
                                     cascade='all, delete-orphan', order_by='CustomOrderStatusHistory.changed_at')
    messages = db.relationship('CustomOrderMessage', back_populates='custom_order', cascade='all, delete-orphan',
                               order_by='CustomOrderMessage.created_at')

    def __repr__(self):
        return f'<CustomOrder {self.id}>'


class OrderStatusHistory(db.Model):
    """История изменения статусов заказа."""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', back_populates='status_history')

    def __repr__(self):
        return f'<OrderStatusHistory {self.id} - {self.status}>'


class CustomOrderStatusHistory(db.Model):
    """История изменения статусов индивидуальной заявки."""
    id = db.Column(db.Integer, primary_key=True)
    custom_order_id = db.Column(db.Integer, db.ForeignKey('custom_order.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    custom_order = db.relationship('CustomOrder', back_populates='status_history')

    def __repr__(self):
        return f'<CustomOrderStatusHistory {self.id} - {self.status}>'


class CustomOrderMessage(db.Model):
    """Сообщение в чате индивидуальной заявки."""
    id = db.Column(db.Integer, primary_key=True)
    custom_order_id = db.Column(db.Integer, db.ForeignKey('custom_order.id'), nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'admin' или 'customer'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    custom_order = db.relationship('CustomOrder', back_populates='messages')

    def __repr__(self):
        return f'<CustomOrderMessage {self.id}>'


class Review(db.Model):
    """Отзыв покупателя о товаре."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # от 1 до 5
    text = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)  # модерация
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reviews')
    product = db.relationship('Product', backref='reviews')
    image_path = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<Review {self.id} - {self.rating}>'


class EmailSettings(db.Model):
    """Настройки электронной почты (singleton, id=1)."""
    id = db.Column(db.Integer, primary_key=True, default=1)
    mail_server = db.Column(db.String(100), nullable=False, default='smtp.yandex.ru')
    mail_port = db.Column(db.Integer, nullable=False, default=465)
    mail_use_ssl = db.Column(db.Boolean, default=True)
    mail_use_tls = db.Column(db.Boolean, default=False)
    mail_username = db.Column(db.String(100))
    mail_password = db.Column(db.String(200))
    mail_default_sender = db.Column(db.String(100))
    admin_email = db.Column(db.String(100))

    def __repr__(self):
        return '<EmailSettings>'
