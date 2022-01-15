from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import PAGINATOR_NUM_PAGE

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def get_page_obj(request, post_list):
    """Get request and QuerySet object, return page object"""
    paginator = Paginator(post_list, PAGINATOR_NUM_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    """Displays all posts on the site.  For all users."""
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = get_page_obj(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    """Displays all posts of the topic group. For all users."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = get_page_obj(request, post_list)
    context = {'group': group, 'page_obj': page_obj}
    return render(request, template, context)


def profile(request, username):
    """Displays all posts of the selected author. For all users."""
    template = 'posts/profile.html'
    user = request.user
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = get_page_obj(request, post_list)
    following = None
    if user.is_authenticated:
        following = Follow.objects.filter(user=user, author=author).exists()
    context = {'page_obj': page_obj, 'author': author, 'following': following}
    return render(request, template, context)


def post_detail(request, post_id):
    """Displays detailed information about the post. Authorized users only."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comment_list = post.comments.all()
    form = CommentForm()
    context = {'post': post, 'form': form, 'comments': comment_list}
    return render(request, template, context)


@login_required
def post_create(request):
    """Adds a new message. Authorized users only."""
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    context = {'form': form}
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Edit the message. Authorized user - author of post only."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(post)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    context = {'is_edit': True, 'form': form}
    if form.is_valid():
        form.save()
        return redirect(post)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Adds a new comment. Authorized users only."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(post)


@login_required
def follow_index(request):
    """Displays all messages of authors from the user's subscription list.
    Authorized users only.
    """
    template = 'posts/follow_index.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_obj(request, post_list)
    context = {'page_obj': page_obj, 'follow': True, }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Adds this author to subscription list. Authorized users only."""
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user, author=author).exists()
    if not follow and user != author:
        follow_new = Follow(user=user, author=author)
        follow_new.save()
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Deletes this author from subscription list. Authorized users only."""
    user = request.user
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=user, author=author).exists():
        Follow.objects.get(user=user, author=author).delete()
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)
