# book_project/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя и папки static
RUN adduser --disabled-password --gecos '' django-user && \
    mkdir -p /app/static && \
    chown -R django-user:django-user /app && \
    chmod -R 755 /app

USER django-user

# Сбор статики при запуске
EXPOSE 8000

CMD ["gunicorn", "book_project.wsgi:application", "--bind", "0.0.0.0:8000"]