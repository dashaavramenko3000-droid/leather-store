from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Regexp

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class ProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(max=200)])
    product_type = SelectField('Тип изделия', choices=[
        ('Кошелёк', 'Кошелёк'),
        ('Сумка', 'Сумка'),
        ('Обложка для документов', 'Обложка для документов'),
        ('Кардхолдер', 'Кардхолдер')
    ], validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = IntegerField('Цена, руб.', validators=[DataRequired(), NumberRange(min=0)])
    images = MultipleFileField('Фотографии', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

class CheckoutForm(FlaskForm):
    customer_name = StringField('Имя', validators=[
        DataRequired(message='Пожалуйста, укажите ваше имя'),
        Length(max=50, message='Имя не должно превышать 50 символов')
    ])
    customer_email = StringField('Email', validators=[
        DataRequired(message='Пожалуйста, укажите email'),
        Email(message='Введите корректный email')
    ])
    customer_phone = StringField('Телефон', validators=[
        DataRequired(message='Пожалуйста, укажите номер телефона'),
        Length(min=10, max=20, message='Номер телефона должен содержать от 10 до 20 символов'),
        Regexp(r'^\+?[\d\s\-\(\)]+$', message='Введите корректный номер телефона')
    ])
    address = TextAreaField('Адрес доставки', validators=[
        DataRequired(message='Пожалуйста, укажите адрес доставки'),
        Length(max=200, message='Адрес не должен превышать 200 символов')
    ])
    comment = TextAreaField('Комментарий к заказу', validators=[
        Length(max=200, message='Комментарий не должен превышать 200 символов')
    ])
    submit = SubmitField('Оформить заказ')