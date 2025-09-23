# books/views.py
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
import os
from .forms import BookForm
from .utils import *
from django.core.files.uploadedfile import UploadedFile


def index(request):
    books = load_all_books()
    if not books:
        messages.info(request, "Нет сохранённых книг.")
    return render(request, 'books/index.html', {'books': books})


def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            # Собираем данные
            book_data = {
                'title': form.cleaned_data['title'],
                'year': form.cleaned_data['year'],
            }
            if form.cleaned_data['author']:
                book_data['author'] = form.cleaned_data['author']
            if form.cleaned_data['genre']:
                book_data['genre'] = form.cleaned_data['genre']

            # Загружаем существующие книги
            existing_books = []
            if os.path.exists(settings.BOOKS_JSON_DIR):
                for fname in os.listdir(settings.BOOKS_JSON_DIR):
                    if fname.endswith('.json'):
                        path = os.path.join(settings.BOOKS_JSON_DIR, fname)
                        valid, data = validate_json_file(path)
                        if valid:
                            existing_books.extend(data)

            # Добавляем новую книгу
            existing_books.append(book_data)

            # Сохраняем обратно
            save_books_to_json(existing_books)

            messages.success(request, "Книга успешно добавлена!")
            return HttpResponseRedirect(reverse('index'))
    else:
        form = BookForm()

    return render(request, 'books/add_book.html', {'form': form})


def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file: UploadedFile = request.FILES['file']
        filename = uploaded_file.name.lower()

        # Санитизация имени
        safe_filename = sanitize_filename(filename)

        # Определяем тип и путь
        if filename.endswith('.json'):
            save_path = os.path.join(settings.BOOKS_JSON_DIR, safe_filename)
            is_json = True
        else:
            messages.error(request, "Поддерживаются только файлы .json")
            return render(request, 'books/upload.html')

        # Сохраняем временно
        with default_storage.open(save_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Валидация
        if is_json:
            valid, data = validate_json_file(save_path)
        else:
            valid, data = validate_xml_file(save_path)

        if not valid:
            # Удаляем невалидный файл
            if os.path.exists(save_path):
                os.remove(save_path)
            messages.error(request, f"Файл '{uploaded_file.name}' невалиден: {data}")
        else:
            messages.success(request, f"Файл '{uploaded_file.name}' успешно загружен!")
    return render(request, 'books/upload.html')