from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from core.models import BaseModel, PublishModel

MODEL_NAME_LENGTH = 30
User = get_user_model()


class Location(PublishModel):
    """Category model. Adds name field."""

    name = models.CharField('Название места', max_length=256)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        """Set the field name as a string representation of a class."""
        return self.name[:MODEL_NAME_LENGTH]


class Category(PublishModel):
    """Category model. Adds title, description and slug fields."""

    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; разрешены символы '
            'латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        """Set the field title as a string representation of a class."""
        return self.title[:MODEL_NAME_LENGTH]


class Post(PublishModel):
    """Post model.

    Adds title, text, pub_date and image fields.
    Joins Author, Location and Category models.
    """

    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — можно делать '
            'отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации',
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name='Местоположение',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
    )
    image = models.ImageField('Фото', upload_to='post_images', blank=True)

    def __str__(self):
        """Set the field title as a string representation of a class."""
        return self.title[:MODEL_NAME_LENGTH]

    def get_absolute_url(self):
        """Redefine get_absolute_url method."""
        return reverse('blog:post_detail', args=[self.pk])

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
        default_related_name = 'posts'


class Comment(BaseModel):
    """Comment model. Adds text field. Joins Author and Post models."""

    text = models.TextField('Текст')
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        on_delete=models.CASCADE,
    )
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        """Set the field text as a string representation of a class."""
        return self.text[:MODEL_NAME_LENGTH]

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)
        default_related_name = 'comments'
