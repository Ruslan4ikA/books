from django.db import models

class Book(models.Model):
    title = models.CharField("Название", max_length=200)
    year = models.IntegerField("Год издания")
    author = models.CharField("Автор", max_length=200, blank=True, null=True)
    genre = models.CharField("Жанр", max_length=100, blank=True, null=True)
    pages = models.CharField("Количество страниц", max_length=100, blank=True, null=True)
    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        unique_together = ('title', 'author')  # Защита от дубликатов

    def __str__(self):
        return f"{self.title} ({self.author})"
