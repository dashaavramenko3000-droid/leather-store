from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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
    order = db.Column(db.Integer, nullable=False, default=0)  # порядок отображения

    def __repr__(self):
        return f'<ProductImage {self.image_path}>'
