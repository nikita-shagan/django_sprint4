from django.db import models


class BaseModel(models.Model):
    """Abstract model. Adds created_at field."""

    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True


class PublishModel(BaseModel):
    """Abstract model. Adds is_published field."""

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        abstract = True
