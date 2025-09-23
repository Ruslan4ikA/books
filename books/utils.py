import json
import xml.etree.ElementTree as ET
import os
import uuid
from django.core.files.storage import default_storage
from django.conf import settings
from datetime import datetime


def sanitize_filename(filename):
    """Безопасное имя файла"""
    ext = os.path.splitext(filename)[1]
    return f"{uuid.uuid4().hex}{ext}"


def validate_json_file(file_path):
    """Проверка валидности JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return True, data
        elif isinstance(data, dict):
            return True, [data]
        else:
            return False, "JSON должен содержать массив или объект"
    except Exception as e:
        return False, str(e)


def validate_xml_file(file_path):
    """Проверка валидности XML (ожидаем <books><book>...</book></books>)"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        books = []
        for book in root.findall('book'):
            item = {}
            for child in book:
                item[child.tag] = child.text or ""
            books.append(item)
        return True, books
    except Exception as e:
        return False, str(e)


def load_all_books():
    """Загружает все книги из JSON и XML файлов"""
    all_books = []

    # Поддерживаемые поля
    expected_fields = ['title', 'year', 'author', 'genre']

    # Чтение JSON файлов
    if os.path.exists(settings.BOOKS_JSON_DIR):
        for fname in os.listdir(settings.BOOKS_JSON_DIR):
            if fname.endswith('.json'):
                path = os.path.join(settings.BOOKS_JSON_DIR, fname)
                valid, data = validate_json_file(path)
                if valid:
                    all_books.extend(data)
                else:
                    print(f"Invalid JSON file {fname}: {data}")

    # Чтение XML файлов (если нужно)
    if os.path.exists(settings.BOOKS_XML_DIR):
        for fname in os.listdir(settings.BOOKS_XML_DIR):
            if fname.endswith('.xml'):
                path = os.path.join(settings.BOOKS_XML_DIR, fname)
                valid, data = validate_xml_file(path)
                if valid:
                    all_books.extend(data)
                else:
                    print(f"Invalid XML file {fname}: {data}")

    # Нормализация данных: добавляем недостающие поля как прочерк
    normalized_books = []
    for book in all_books:
        normalized = {}
        for field in expected_fields:
            normalized[field] = book.get(field, "—")
            if normalized[field] == "":
                normalized[field] = "—"
        normalized_books.append(normalized)

    return normalized_books


def save_books_to_json(books, filename=None):
    """Сохраняет список книг в JSON файл"""
    if not filename:
        filename = f"books_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(settings.BOOKS_JSON_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)
    return filepath