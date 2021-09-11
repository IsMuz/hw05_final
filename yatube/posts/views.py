from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import paginate


@cache_page(60 * 20)
def index(request):
    """Project main page with all posts listed"""
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = paginate(request, post_list)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    """Posts list sorted by group"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginate(request, posts)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    """Profile page with user posts"""
    author = get_object_or_404(User, username=username)
    #
    # f = Follow.objects.filter(
    #     user=request.user,
    #     author=author
    # ).exists()
    # if f or request.user.is_authenticated:
    #     following = True
    # elif request.user.is_authenticated:
    #     following = False
    post_all = author.posts.all()
    page_obj = paginate(request, post_all)
    context = {
        'author': author,
        'page_obj': page_obj,
        # 'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Post detailed information"""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Post creation form"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect(
                reverse(
                    'posts:profile',
                    kwargs={
                        'username': request.user.username
                    }
                )
            )
        return render(request, 'posts/post_create.html', {"form": form})
    form = PostForm()
    return render(request, 'posts/post_create.html', {"form": form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post_inst = get_object_or_404(Post, pk=post_id)
    if request.user == post_inst.author:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post_inst
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
        context = {
            "form": form,
            'post': post_inst,
            'is_edit': is_edit
        }
        return render(request, 'posts/post_create.html', context)
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    # ...
    # posts = Post.objects.filter(author=request.user)
    follows = Follow.objects.filter(user=request.user)
    posts = Post.objects.filter(author__following__in=follows)
    # posts = []
    #
    # for follow in follows:
    #     user = User.objects.get(following=follow)
    #     posts.append(user.posts.all())
    page_obj = paginate(request, posts)
    context = {
        # 'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    obj = Follow(
        user=request.user,
        author=author
    )
    f = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if request.user != author and f is False:
        obj.save()
    else:
        return redirect('posts/profile.html', username)
    return render(request, 'posts/index.html')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author).delete()
    # return redirect(request, 'posts/index.html')
    return render(request, 'posts/index.html')
