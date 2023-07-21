from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone as tz
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.views.generic.detail import BaseDetailView

from blog.forms import CommentForm, PostForm
from blog.models import Category, Comment, Post, User

POSTS_PER_PAGE = 10


class PostObjects:
    """Class encapsulates manipulations with the queryset of Post model."""

    posts = Post.objects

    def add_related(self):
        """Join related models."""
        self.posts = self.posts.select_related(
            'author', 'location', 'category'
        )
        return self

    def add_comments(self):
        """Annotate posts with comments."""
        self.posts = (
            self.posts
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )
        return self

    def exclude_unpublished(self):
        """Exclude unpublished posts and those with unpublished category."""
        self.posts = self.posts.filter(
            pub_date__lte=tz.now(),
            is_published=True,
            category__is_published=True
        )
        return self

    def apply_all_filters(self):
        """Apply filters: add related, add comments, exclude unpublished."""
        self.add_related().add_comments().exclude_unpublished()
        return self

    def get_all(self):
        """Return queryset of posts."""
        return self.posts


class PostCreateView(LoginRequiredMixin, CreateView):
    """CreateView class for creating posts."""

    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        """Set post's author in form instance."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Redefine success_url to post's author profile page."""
        return reverse('blog:profile', args=[self.request.user.username])


class PostObjectMixin(BaseDetailView, PostObjects):
    """Define post model attribute and get_object method."""

    model = Post

    def get_object(self, queryset=None):
        """Reduce the amount of queries to database."""
        return get_object_or_404(
            self.add_related().get_all(),
            pk=self.kwargs.get('post_id')
        )


class PostDetailView(PostObjectMixin, DetailView):
    """DetailView class with particular post."""

    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        """Allow only post creator to see a post which isn't published."""
        post = self.get_object()
        if (
            post.author != request.user
            and (
                not post.is_published
                or post.pub_date > tz.now()
            )
        ):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add form and comments to context."""
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('author')
        context['form'] = CommentForm()
        return context


class PostProtectedMixin(LoginRequiredMixin, PostObjectMixin):
    """Protected post view."""

    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        """Protect post by owner checking."""
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', kwargs['post_id'])

        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(PostProtectedMixin, UpdateView):
    """UpdateView class for updating posts."""

    form_class = PostForm


class PostDeleteView(PostProtectedMixin, DeleteView):
    """DeleteView class for deleting posts."""

    def get_context_data(self, **kwargs):
        """Add post form to context."""
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self, **kwargs):
        """Redefine success_url to profile page."""
        return reverse('blog:profile', args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    """CreateView class for adding comments to Posts."""

    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'post_id'
    post_instance = None

    def form_valid(self, form):
        """Set post_instance and add it and author to form instance."""
        self.post_instance = self.get_object(Post.objects)
        form.instance.author = self.request.user
        form.instance.post = self.post_instance
        return super().form_valid(form)

    def get_success_url(self):
        """Redefine success_url to post detail page."""
        return reverse('blog:post_detail', args=[self.post_instance.pk])


class CommentProtectedView(LoginRequiredMixin, BaseDetailView):
    """Protected View.

    Protect comment and define get_object and get_success_url methods.
    Set model, template_name and pk_url_kwarg attributes.
    """

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        """Protect comment by owner checking."""
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', kwargs['post_id'])

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Reduce the amount of queries to database."""
        return get_object_or_404(
            Comment.objects.select_related('author'),
            pk=self.kwargs.get('comment_id')
        )

    def get_success_url(self, **kwargs):
        """Redefine success_url to post detail page."""
        return reverse('blog:post_detail', args=[self.object.post.pk])


class CommentUpdateView(CommentProtectedView, UpdateView):
    """UpdateView class for editing comments."""

    form_class = CommentForm


class CommentDeleteView(CommentProtectedView, DeleteView):
    """DeleteView class for deleting comments."""

    pass


class CategoryPostsListView(ListView, PostObjects):
    """ListView class with posts in particular category."""

    model = Post
    template_name = 'blog/category.html'
    paginate_by = POSTS_PER_PAGE
    category = None

    def get_queryset(self):
        """Rewrite queryset and set category attribute."""
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs.get('category_slug'),
            is_published=True
        )
        return (
            self
            .apply_all_filters()
            .get_all()
            .filter(category=self.category)
        )

    def get_context_data(self, **kwargs):
        """Add category model to context."""
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfilePostsListView(ListView, PostObjects):
    """ListView class with posts created by particular author."""

    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE
    author = None

    def get_queryset(self):
        """Set author attribute and rewrite queryset."""
        self.author = get_object_or_404(
            User,
            username=self.kwargs.get('username')
        )

        posts = self.add_related().add_comments()
        return (
            posts.get_all()
            if self.request.user == self.author
            else posts.exclude_unpublished().get_all()
        ).filter(author=self.author)

    def get_context_data(self, **kwargs):
        """Add user model to context."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """UpdateView class for updating user profile."""

    model = User
    template_name = 'blog/user.html'
    fields = ('username', 'first_name', 'last_name', 'email')

    def get_object(self, queryset=None):
        """Redefine get_object to return user who made request."""
        return self.request.user

    def get_success_url(self):
        """Redefine success_url to user's profile page."""
        return reverse('blog:profile', args=[self.request.user.username])


class IndexListView(ListView):
    """ListView class with all published posts."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_PER_PAGE
    queryset = PostObjects().apply_all_filters().get_all()
