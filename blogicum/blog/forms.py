from django import forms

from blog.models import Comment, Post


class PostForm(forms.ModelForm):
    """Form class based on Post model."""

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%d %H:%M:%S',
                attrs={'type': 'datetime-local'}
            )
        }


class CommentForm(forms.ModelForm):
    """From class based on Comment model with only text field."""

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 5})
        }
