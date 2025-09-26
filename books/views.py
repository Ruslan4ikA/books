# books/views.py
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
import os
from .forms import BookForm
from .utils import *
from django.core.files.uploadedfile import UploadedFile
from .utils import (
    sanitize_filename, validate_json_file,
    load_all_books_from_file, save_all_books_to_file
)


def index(request):
    books = load_all_books()
    if not books:
        messages.info(request, "Нет сохранённых книг.")
    return render(request, 'books/index.html', {'books': books})


# books/views.py

def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            # Собираем данные новой книги
            new_book = {
                'title': form.cleaned_data['title'].strip(),
                'year': form.cleaned_data['year'],  # int
            }
            if form.cleaned_data['author']:
                new_book['author'] = form.cleaned_data['author'].strip()
            if form.cleaned_data['genre']:
                new_book['genre'] = form.cleaned_data['genre'].strip()

            # Загружаем существующие книги
            all_books = load_all_books_from_file()

            # Проверяем дубликат: совпадение по title и year
            is_duplicate = any(
                book.get('title') == new_book['title'] and
                book.get('year') == new_book['year']
                for book in all_books
            )

            if is_duplicate:
                messages.warning(request, f"Книга '{new_book['title']}' ({new_book['year']}) уже существует.")
            else:
                all_books.append(new_book)
                save_all_books_to_file(all_books)
                messages.success(request, "Книга успешно добавлена!")

            return HttpResponseRedirect(reverse('books:index'))
    else:
        form = BookForm()

    return render(request, 'books/add_book.html', {'form': form})


def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()

        # Поддерживаем только JSON
        if not (filename.endswith('.json')):
            messages.error(request, "Поддерживаются только файлы .json")
            return render(request, 'books/upload.html')

        # Временное сохранение
        safe_filename = sanitize_filename(filename)
        temp_path = os.path.join(settings.BOOKS_JSON_DIR, safe_filename)  # можно в любую папку

        with open(temp_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        # Валидация файла
        if filename.endswith('.json'):
            valid, data_or_error = validate_json_file(temp_path)

        # Удаляем временный файл сразу после проверки
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not valid:
            messages.error(request, f"Загрузка отменена. {data_or_error}")
            return render(request, 'books/upload.html')

        # Теперь data_or_error — это список книг
        new_books = data_or_error

        # Загружаем существующие книги
        all_books = load_all_books_from_file()

        # Добавляем новые (можно проверить на дубликаты по title+year, если нужно)
        initial_count = len(all_books)
        for book in new_books:
            # Простая защита от полных дубликатов (по названию и году)
            if not any(b.get('title') == book['title'] and b.get('year') == book['year'] for b in all_books):
                all_books.append(book)

        added_count = len(all_books) - initial_count
        if added_count == 0:
            messages.success(request,
                         f"Файл '{uploaded_file.name}' не загружен. Книга с таким названием и годом уже существует")
        else:
            # Сохраняем всё в один файл
            save_all_books_to_file(all_books)

            messages.success(request,
                             f"Файл '{uploaded_file.name}' успешно загружен. Добавлено книг: {added_count}. Всего в базе: {len(all_books)}.")

    return render(request, 'books/upload.html')