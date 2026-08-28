from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileAllowed, FileField
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField, IntegerField, BooleanField
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
    """Форма заявки на индивидуальный заказ (с возможностью прикрепить фото)."""
    name = StringField('Ваше имя', validators=[DataRequired(), Length(max=100)])
    contact = StringField('Email или телефон', validators=[DataRequired(), Length(max=100)])
    product_type = SelectField('Тип изделия', choices=[
        ('', 'Выберите тип...'),
        ('Кошелёк', 'Кошелёк'),
        ('Сумка', 'Сумка'),
        ('Обложка для документов', 'Обложка для документов'),
        ('Кардхолдер', 'Кардхолдер'),
        ('Другое', 'Другое')
    ], validators=[Optional()])
    description = TextAreaField('Опишите вашу идею', validators=[DataRequired(), Length(max=1000)])
    image = FileField('Фото изделия', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
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