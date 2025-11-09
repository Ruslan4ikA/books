# scripts/migrate_sqlite_to_postgres.py

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'book_project.settings')

import django
django.setup()

import sqlite3
from books.models import Book

# Пути к старой базе
SQLITE_DB_PATH = '/app/db.sqlite3'  # внутри контейнера

print("🔌 Подключение к SQLite...")
try:
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cur = sqlite_conn.cursor()
except Exception as e:
    print(f"❌ Ошибка подключения к SQLite: {e}")
    exit(1)

print("✅ Подключение к PostgreSQL через Django ORM")
added = 0
errors = 0

sqlite_cur.execute("SELECT title, year, author, genre, pages FROM books_book")
rows = sqlite_cur.fetchall()

for row in rows:
    try:
        title, year, author, genre, pages = row
        book, created = Book.objects.update_or_create(
            title=title.strip(),
            year=year,
            defaults={
                'author': author.strip() if author else None,
                'genre': genre.strip() if genre else None,
                'pages': pages.strip() if pages else None,
            }
        )
        if created:
            print(f"✅ Добавлено: {title} ({year})")
            added += 1
        else:
            print(f"🔄 Обновлено: {title} ({year})")
    except Exception as e:
        print(f"❌ Ошибка при добавлении {row}: {e}")
        errors += 1

print(f"\n📊 Готово: {added} книг добавлено, {errors} ошибок.")