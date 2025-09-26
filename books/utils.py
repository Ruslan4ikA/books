import json
import os
import uuid
from django.core.files.storage import default_storage
from django.conf import settings
from datetime import datetime

ALL_BOOKS_FILE = os.path.join(settings.BOOKS_JSON_DIR, 'all_books.json')

def sanitize_filename(filename):
    """Безопасное имя файла"""
    ext = os.path.splitext(filename)[1]
    return f"{uuid.uuid4().hex}{ext}"

def validate_book_data(book, file_source, index=None):
    """
    Проверяет одну книгу на наличие обязательных полей.
    Возвращает (успех, сообщение)
    """
    # Проверка title
    title = book.get('title')
    if not title or not str(title).strip():
        name = f"элемента {index}" if index is not None else ""
        return False, f"В {file_source} у {name} отсутствует или пустое поле 'title'"

    # Проверка year
    year_val = book.get('year')
    if year_val is None:
        name = f"элемента {index}" if index is not None else ""
        return False, f"В {file_source} у {name} отсутствует поле 'year'"

    try:
        year = int(year_val)
        if year < 0 or year > 2025:
            return False, f"Поле 'year' должно быть от 0 до 2025, получено: {year}"
    except (ValueError, TypeError):
        return False, f"Поле 'year' должно быть числом, получено: {year_val}"

    return True, ""

def validate_json_file(file_path):
    """Проверяет JSON-файл: структура + валидация каждой книги"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return False, "JSON должен содержать объект или массив объектов"

        # Проверяем каждую книгу
        for i, book in enumerate(data):
            if not isinstance(book, dict):
                return False, f"Книга #{i+1} не является объектом (словарём)"

            valid, msg = validate_book_data(book, "JSON", i+1)
            if not valid:
                return False, msg

        return True, data

    except Exception as e:
        return False, f"Ошибка чтения JSON: {str(e)}"


def load_all_books():
    """Загружает все книги из общего файла и нормализует поля"""
    books = load_all_books_from_file()
    expected_fields = ['title', 'year', 'author', 'genre']

    normalized = []
    for book in books:
        norm = {}
        for field in expected_fields:
            value = book.get(field, None)

            # Если значение отсутствует или None
            if value is None or value == "":
                norm[field] = "—"
            else:
                # Преобразуем в строку и обрезаем пробелы только если это строка
                if isinstance(value, str):
                    cleaned = value.strip()
                    norm[field] = cleaned if cleaned else "—"
                else:
                    # Для чисел, булевых и др. — просто в строку
                    norm[field] = str(value)
        normalized.append(norm)

    return normalized

def save_book_as_json(book_data):
    """Сохраняет одну книгу в отдельный JSON-файл"""
    # Генерируем уникальное имя файла
    filename = f"book_{uuid.uuid4().hex}.json"
    filepath = os.path.join(settings.BOOKS_JSON_DIR, filename)

    # Создаём директорию, если её нет
    os.makedirs(settings.BOOKS_JSON_DIR, exist_ok=True)

    # Сохраняем одну книгу в файл
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(book_data, f, ensure_ascii=False, indent=4)

    return filepath

def load_all_books_from_file():
    """Читает все книги из общего файла all_books.json"""
    if not os.path.exists(ALL_BOOKS_FILE):
        return []
    try:
        with open(ALL_BOOKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except Exception:
        return []


def save_all_books_to_file(books):
    """Сохраняет список книг в общий файл"""
    os.makedirs(os.path.dirname(ALL_BOOKS_FILE), exist_ok=True)
    with open(ALL_BOOKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)