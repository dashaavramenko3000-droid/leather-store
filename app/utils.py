import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app


def create_upload_folder(app):
    """Создаёт папку для загрузок, если её нет"""
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)


def save_image(file):
    """Сохраняет изображение в папку uploads, сжимает и возвращает относительный путь."""
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)

    try:
        img = Image.open(file)
        img.thumbnail((1200, 1200))
        img.save(file_path, optimize=True, quality=85)
    except Exception as e:
        current_app.logger.error(f'Ошибка сохранения изображения: {e}')
        return None

    return 'uploads/' + unique_name


def delete_image_file(image_path):
    """Удаляет файл изображения с диска."""
    if not image_path or image_path.startswith('http'):
        return
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_path.replace('uploads/', '', 1))
    if os.path.exists(full_path):
        os.remove(full_path)
