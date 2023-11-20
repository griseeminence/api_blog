from django.contrib import admin

from .models import Category, CustomUser, Genre, Title


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'year',
        'description',
        'category'
    )
    list_editable = (
        'category',
    )
    list_filter = (
        'category',
        'genre'
    )


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'role',
        'bio'
    )
    list_edit = (
        'role',
        'first_name',
        'last_name',
        'bio',
    )
    search_fields = (
        'email',
        'username',
        'role'
    )
