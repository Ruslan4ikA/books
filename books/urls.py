# books/urls.py
from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_book, name='add_book'),
    path('upload/', views.upload_file, name='upload_file'),
]