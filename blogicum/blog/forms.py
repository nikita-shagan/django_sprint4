from django import forms

from blog.models import Comment, Post


class PostForm(forms.ModelForm):
    """Form class based on Post model."""

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'})
        }


class CommentForm(forms.ModelForm):
    """From class based on Comment model with only text field."""

    class Meta:
        model = Comment
        fields = ('text',)
