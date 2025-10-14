import os
from .utils import *
from django.core.files.uploadedfile import UploadedFile
from .utils import (
    sanitize_filename, validate_json_file,
    load_all_books_from_file, save_all_books_to_file
)
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from .models import Book
from .forms import BookForm
from .utils import load_all_books


def index(request):
    source = request.GET.get('source', 'file')  # 'file' или 'db'

    if source == 'db':
        books = list(Book.objects.all().values())
        db_active = True
    else:
        books = load_all_books()
        db_active = False

    return render(request, 'books/index.html', {
        'books': books,
        'db_active': db_active,
        'source': source
    })

def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            # Собираем данные новой книги
            title = form.cleaned_data['title'].strip()
            year = form.cleaned_data['year']
            author = form.cleaned_data['author'].strip() if form.cleaned_data['author'] else None
            genre = form.cleaned_data['genre'].strip() if form.cleaned_data['genre'] else None
            pages = form.cleaned_data['pages'].strip() if form.cleaned_data['pages'] else None

            # Получаем выбор пользователя: куда сохранять
            save_to = form.cleaned_data['save_to']

            if save_to == 'db':
                # Сохранение в базу данных SQLite
                if Book.objects.filter(title=title, author=author).exists():
                    messages.warning(request, f"Книга '{title}' ({author}) уже существует в базе данных.")
                else:
                    Book.objects.create(
                        title=title,
                        year=year,
                        author=author,
                        genre=genre,
                        pages=pages
                    )
                    messages.success(request, "Книга успешно добавлена в базу данных!")
            else:
                # Сохранение в файл JSON (старая логика)
                all_books = load_all_books_from_file()

                new_book = {
                    'title': title,
                    'year': year,
                }
                if author:
                    new_book['author'] = author
                if genre:
                    new_book['genre'] = genre
                if pages:
                    new_book['pages'] = pages

                # Проверяем дубликат по названию и году
                is_duplicate = any(
                    book.get('title') == new_book['title'] and
                    book.get('year') == new_book['year']
                    for book in all_books
                )

                if is_duplicate:
                    messages.warning(request, f"Книга '{new_book['title']}' ({new_book['year']}) уже существует в файлах.")
                else:
                    all_books.append(new_book)
                    save_all_books_to_file(all_books)
                    messages.success(request, "Книга успешно добавлена в файл!")

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
            # Простая защита от полных дубликатов (по названию и автору)
            if not any(b.get('title') == book['title'] and b.get('author') == book['author'] for b in all_books):
                all_books.append(book)

        added_count = len(all_books) - initial_count
        if added_count == 0:
            messages.success(request,
                         f"Файл '{uploaded_file.name}' не загружен. Книга с таким названием и автором уже существует")
        else:
            # Сохраняем всё в один файл
            save_all_books_to_file(all_books)

            messages.success(request,
                             f"Файл '{uploaded_file.name}' успешно загружен. Добавлено книг: {added_count}. Всего в базе: {len(all_books)}.")

    return render(request, 'books/upload.html')

def search_books(request):
    query = request.GET.get('q', '')
    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).values()
    else:
        books = Book.objects.all().values()
    return JsonResponse(list(books), safe=False)


def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST)
        print(form['title'])
        if form:
            title = form.cleaned_data['title']
            year = form.cleaned_data['year']
            author = form.cleaned_data['author'] or None
            genre = form.cleaned_data['genre'] or None
            pages = form.cleaned_data['pages'] or None

            # Проверка дубликата (кроме самой книги)
            if Book.objects.exclude(pk=pk).filter(title=title, year=year).exists():
                return JsonResponse({'success': False, 'error': 'Такая книга уже существует.'})

            book.title = title
            book.year = year
            book.author = author
            book.genre = genre
            book.pages = pages
            book.save()

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Проверьте корректность данных. Возможно такая книга уже есть или не заполнено обязательное поле'})
    return JsonResponse({'success': False}, status=405)


def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return JsonResponse({'success': True})