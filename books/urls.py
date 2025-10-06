# books/urls.py
from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_book, name='add_book'),
    path('upload/', views.upload_file, name='upload_file'),
    path('edit/<int:pk>/', views.edit_book, name='edit_book'),
    path('delete/<int:pk>/', views.delete_book, name='delete_book'),
    path('search/', views.search_books, name='search_books'),
]