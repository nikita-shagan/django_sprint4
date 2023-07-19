from django.contrib import admin

from .models import Category, Location, Post


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin settings for Location model."""

    list_display = (
        'name',
        'is_published',
        'created_at',
    )
    list_editable = (
        'is_published',
    )
    search_fields = ('name',)
    list_filter = ('is_published',)
    list_display_links = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin settings for Category model."""

    list_display = (
        'title',
        'description',
        'slug',
        'is_published',
        'created_at',
    )
    list_editable = (
        'is_published',
    )
    search_fields = ('title',)
    list_filter = ('is_published',)
    list_display_links = ('title',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin settings for Post model."""

    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at',
    )
    list_editable = (
        'is_published',
        'category',
    )
    search_fields = ('title',)
    list_filter = ('category', 'is_published',)
    list_display_links = ('title',)
