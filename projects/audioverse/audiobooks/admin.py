from django.contrib import admin
from .models import Author, Narrator, Genre, Audiobook

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Narrator)
class NarratorAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Audiobook)
class AudiobookAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'duration_formatted', 'average_rating', 'created_at']
    search_fields = ['title', 'isbn']
    list_filter = ['language', 'genres']
    filter_horizontal = ['authors', 'narrators', 'genres']