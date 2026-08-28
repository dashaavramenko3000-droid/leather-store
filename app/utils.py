import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app


def create_upload_folder(app):
    """
    Создаёт папку для загрузки изображений, если она ещё не существует.

    :param app: Flask-приложение, из конфигурации которого берётся путь к папке.
    """
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)


def save_image(file):
    """
    Сохраняет загруженное изображение в папку загрузок, предварительно сжимая его.

    Возвращает относительный путь к сохранённому файлу (например, 'uploads/abc.jpg')
    или None, если файл не был передан или произошла ошибка сохранения.

    :param file: объект FileStorage из Flask-WTF/Werkzeug
    :return: str или None
    """
    # Проверяем, что файл действительно передан и имеет имя
    if not file or not file.filename:
        return None

    # Обезопасиваем имя файла (убираем опасные символы, пути)
    filename = secure_filename(file.filename)

    # Генерируем уникальное имя, чтобы избежать перезаписи существующих файлов
    unique_name = f"{uuid.uuid4().hex}_{filename}"

    # Полный путь к будущему файлу в папке загрузок
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)

    try:
        # Открываем изображение с помощью Pillow
        img = Image.open(file)
        # Уменьшаем до максимального размера 1200x1200, сохраняя пропорции
        img.thumbnail((1200, 1200))
        # Сохраняем с оптимизацией и качеством 85%
        img.save(file_path, optimize=True, quality=85)
    except Exception as e:
        # Логируем ошибку и возвращаем None
        current_app.logger.error(f'Ошибка сохранения изображения: {e}')
        return None

    # Возвращаем относительный путь для хранения в БД или отображения
    return 'uploads/' + unique_name


def delete_image_file(image_path):
    """
    Удаляет файл изображения с диска, если он существует.

    Не удаляет внешние изображения (если путь начинается с http).

    :param image_path: относительный путь, например 'uploads/abc.jpg'
    """
    # Игнорируем пустые пути и внешние ссылки
    if not image_path or image_path.startswith('http'):
        return

    # Получаем полный путь к файлу, убирая префикс 'uploads/'
    full_path = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        image_path.replace('uploads/', '', 1)
    )

    # Если файл существует, удаляем его
    if os.path.exists(full_path):
        os.remove(full_path)