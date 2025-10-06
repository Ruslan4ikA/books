# books/forms.py
from django import forms

class BookForm(forms.Form):
    title = forms.CharField(label="Название", max_length=200)
    year = forms.IntegerField(label="Год издания", min_value=0, max_value=2025)
    author = forms.CharField(label="Автор", max_length=200, required=False)
    genre = forms.CharField(label="Жанр", max_length=100, required=False)
    pages = forms.CharField(label="Количество страниц",  max_length=100, required=False)