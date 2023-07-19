from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone as tz
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from blog.forms import CommentForm, PostForm
from blog.models import Category, Comment, Post

POSTS_PER_PAGE = 10


def get_all_posts():
    """Return all posts with all joined models."""
    return (
        Post.objects.select_related('author', 'location', 'category')
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )


def get_published_posts():
    """Return already published posts with all joined models."""
    return get_all_posts().filter(
        pub_date__lte=tz.now(),
        is_published=True,
        category__is_published=True
    )


class PostCreateView(LoginRequiredMixin, CreateView):
    """CreateView class for creating posts."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        """Redefine success_url to post's author profile page."""
        return reverse_lazy('blog:profile', args=[self.request.user.username])

    def form_valid(self, form):
        """Set post's author in form instance."""
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDetailView(DetailView):
    """DetailView class with particular post."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        """Allow only post creator to see post which isn't published."""
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        not_owner = post.author != request.user
        if not_owner and (not post.is_published or post.pub_date > tz.now()):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add form and comments to context."""
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('author')
        context['form'] = CommentForm()
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """UpdateView class for updating posts."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        """Protect post editing by owner checking."""
        post_id = kwargs['post_id']
        post_object = get_object_or_404(Post, pk=post_id)
        if post_object.author != request.user:
            return redirect('blog:post_detail', post_id)

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        """Redefine success_url to post detail page."""
        return reverse_lazy('blog:post_detail', args=[self.object.pk])


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """DeleteView class for deleting posts."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        """Protect post deleting by owner checking."""
        post_id = kwargs['post_id']
        post_object = get_object_or_404(Post, pk=post_id)
        if post_object.author != request.user:
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        """Redefine success_url to profile page."""
        return reverse_lazy('blog:profile', args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    """CreateView class for adding comments to Posts."""

    post_instance = None
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        """Set post attribute."""
        self.post_instance = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Set autor and post attributes to form instance."""
        form.instance.author = self.request.user
        form.instance.post = self.post_instance
        return super().form_valid(form)

    def get_success_url(self):
        """Redefine success_url to post detail page."""
        return reverse('blog:post_detail', args=[self.post_instance.pk])


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """UpdateView class for editing comments."""

    form_class = CommentForm
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        """Protect comment editing by owner checking."""
        comment_object = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if comment_object.author != request.user:
            return redirect('blog:post_detail', kwargs['post_id'])

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        """Redefine success_url to post detail page."""
        return reverse_lazy('blog:post_detail', args=[self.object.post.pk])


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """DeleteView class for deleting comments."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        """Protect comment deleting by owner checking."""
        comment_object = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if comment_object.author != request.user:
            return redirect('blog:post_detail', kwargs['post_id'])

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        """Redefine success_url to post detail page."""
        return reverse_lazy('blog:post_detail', args=[self.object.post.pk])


class CategoryPostsListView(ListView):
    """ListView class with posts in particular category."""

    model = Post
    paginate_by = POSTS_PER_PAGE
    template_name = 'blog/category.html'
    category = None

    def dispatch(self, request, *args, **kwargs):
        """Set category attribute and rewrite queryset."""
        self.category = get_object_or_404(
            Category,
            slug=kwargs['category_slug'],
            is_published=True
        )
        self.queryset = get_published_posts().filter(category=self.category)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add category model to context."""
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfilePostsListView(ListView):
    """ListView class with posts created by particular author."""

    model = Post
    paginate_by = POSTS_PER_PAGE
    template_name = 'blog/profile.html'
    author = None

    def dispatch(self, request, *args, **kwargs):
        """Set author attribute and rewrite queryset."""
        self.author = get_object_or_404(
            get_user_model(),
            username=kwargs['username']
        )
        self.queryset = (
            get_all_posts()
            if request.user == self.author
            else get_published_posts()
        ).filter(author=self.author)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add user model to context."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """UpdateView class for updating user profile."""

    model = get_user_model()
    fields = ('username', 'first_name', 'last_name', 'email')
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def dispatch(self, request, *args, **kwargs):
        """Protect profile editing by owner checking."""
        user = get_object_or_404(get_user_model(), username=kwargs['username'])
        if user != request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Redefine success_url to user's profile page."""
        return reverse_lazy('blog:profile', args=[self.request.user.username])


class IndexListView(ListView):
    """ListView class with all published posts."""

    model = Post
    queryset = get_published_posts()
    paginate_by = POSTS_PER_PAGE
    template_name = 'blog/index.html'
