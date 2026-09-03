from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileAllowed, FileField
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField, IntegerField, BooleanField, \
    FloatField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Regexp, EqualTo, Optional


# ======================================================================
#  АДМИНИСТРАТИВНАЯ ЧАСТЬ
# ======================================================================

class LoginForm(FlaskForm):
    """Форма входа в админ-панель (по логину)."""
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class ProductForm(FlaskForm):
    """Форма добавления/редактирования товара (с несколькими фото)."""
    name = StringField('Название', validators=[DataRequired(), Length(max=200)])
    product_type = SelectField('Тип изделия', choices=[
        ('Кошелёк', 'Кошелёк'),
        ('Сумка', 'Сумка'),
        ('Обложка для документов', 'Обложка для документов'),
        ('Кардхолдер', 'Кардхолдер')
    ], validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = IntegerField('Цена, руб.', validators=[DataRequired(), NumberRange(min=0)])
    material = StringField('Материал', validators=[Length(max=100)])
    color = StringField('Цвет', validators=[Length(max=100)])
    dimensions = StringField('Размеры', validators=[Length(max=100)])
    weight = FloatField('Вес, кг', validators=[Optional()])
    images = MultipleFileField('Фотографии', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')


# ======================================================================
#  ПОКУПАТЕЛЬСКАЯ ЧАСТЬ
# ======================================================================

class CustomerLoginForm(FlaskForm):
    """Форма входа для покупателей (по email или имени пользователя)."""
    email_or_username = StringField('Email или логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """Форма регистрации нового покупателя."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Повторите пароль', validators=[
        DataRequired(),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    full_name = StringField('Имя', validators=[Length(max=100)])
    phone = StringField('Телефон', validators=[Length(max=20)])
    address = TextAreaField('Адрес', validators=[Length(max=200)])
    submit = SubmitField('Зарегистрироваться')


class UpdateProfileForm(FlaskForm):
    """Форма редактирования профиля покупателя."""
    full_name = StringField('Имя', validators=[Length(max=100)])
    phone = StringField('Телефон', validators=[Length(max=20)])
    address = TextAreaField('Адрес', validators=[Length(max=200)])
    submit = SubmitField('Сохранить')


class CheckoutForm(FlaskForm):
    """Форма оформления заказа (контактные данные и адрес)."""
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


class CustomOrderForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    product_type = SelectField('Тип изделия', choices=[
        ('', 'Выберите тип...'),
        ('Кошелёк', 'Кошелёк'),
        ('Сумка', 'Сумка'),
        ('Обложка для документов', 'Обложка для документов'),
        ('Кардхолдер', 'Кардхолдер'),
        ('Другое', 'Другое')
    ], validators=[Optional()])
    description = TextAreaField('Идея', validators=[DataRequired(), Length(max=1000)])
    image = FileField('Фото изделия', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
    ])
    accept_terms = BooleanField('Я согласен с условиями индивидуального заказа', validators=[
        DataRequired(message='Необходимо согласиться с условиями')
    ])
    submit = SubmitField('Отправить заявку')


class ResetPasswordRequestForm(FlaskForm):
    """Форма запроса на сброс пароля (ввод email)."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Отправить')


class ResetPasswordForm(FlaskForm):
    """Форма установки нового пароля."""
    password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Повторите пароль', validators=[
        DataRequired(),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Сохранить')


class ReviewForm(FlaskForm):
    rating = SelectField('Оценка', choices=[(str(i), str(i)) for i in range(1, 6)], validators=[DataRequired()])
    text = TextAreaField('Отзыв', validators=[DataRequired(), Length(max=1000)])
    image = FileField('Фото', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')])
    submit = SubmitField('Оставить отзыв')


class EmailSettingsForm(FlaskForm):
    mail_server = StringField('SMTP сервер', validators=[DataRequired()])
    mail_port = IntegerField('Порт', validators=[DataRequired()])
    mail_use_ssl = BooleanField('Использовать SSL')
    mail_use_tls = BooleanField('Использовать TLS')
    mail_username = StringField('Логин')
    mail_password = PasswordField('Пароль')
    mail_default_sender = StringField('Email отправителя')
    admin_email = StringField('Email администратора (для уведомлений)')
    submit = SubmitField('Сохранить')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Повторите новый пароль', validators=[
        DataRequired(),
        EqualTo('new_password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Сохранить новый пароль')


class AddressForm(FlaskForm):
    address_line = StringField('Адрес (улица, дом, квартира)', validators=[DataRequired(), Length(max=200)])
    city = StringField('Город', validators=[DataRequired(), Length(max=100)])
    postal_code = StringField('Почтовый индекс', validators=[Optional(), Length(max=20)])
    is_default = BooleanField('Сделать адресом по умолчанию')
    submit = SubmitField('Сохранить')
