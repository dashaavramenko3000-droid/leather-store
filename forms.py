from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Email


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
    price = IntegerField('Цена, руб.',
                         validators=[DataRequired(), NumberRange(min=0, message='Цена не может быть отрицательной')])
    images = MultipleFileField('Фотографии', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

    class CheckoutForm(FlaskForm):
        customer_name = StringField('Имя', validators=[DataRequired(), Length(max=100)])
        customer_email = StringField('Email', validators=[DataRequired(), Email()])
        customer_phone = StringField('Телефон', validators=[DataRequired(), Length(max=30)])
        address = TextAreaField('Адрес доставки')
        submit = SubmitField('Оформить заказ')
