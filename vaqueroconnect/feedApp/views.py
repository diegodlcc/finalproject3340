from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .models import Post, Comment, Profile

# This is the Homepage
def home(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        content = request.POST.get('tweet_content', '').strip()
        if content:
            Post.objects.create(author=request.user, content=content)
        return redirect('home')

    posts = Post.objects.all()
    return render(request, 'index.html', {'posts': posts})

# This is the Account Management page
@login_required
def account(request):
    Profile.objects.get_or_create(user=request.user)

    # Ask databse for posts where autho is the current user
    my_posts = Post.objects.filter(author=request.user).order_by('-created_at')

    # Posts the user commented on
    commented_posts = Post.objects.filter(
        comments__author=request.user
    ).exclude(
        author=request.user
    ).distinct().order_by('-created_at')

    context = {
        'my_posts': my_posts,
        'commented_posts' : commented_posts,
    }
    return render(request, 'account.html', context)

# This is account creation
def signup(request):
    # 1. If the user clicks the "Sign Up" button (sending data to the server)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        # 2. Django checks if the username is taken or passwords don't match
        if form.is_valid():
            # 3. Save user to database
            user = form.save()
            # 4. Automatically log the user in right after they sign up
            auth_login(request, user)
            # 5. Send them to the homepage
            return redirect('home')
    # 6. If they are just visiting the page for the first time, show a blank form
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})

# Delete a post (only the author can delete)
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
    return redirect('home')

# Edit a post (only the author can edit)
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            post.content = content
            post.save()
    return redirect('home')

# Like or unlike a post
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.likes.filter(id=request.user.id).exists():
        # Unlike if already liked
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# Add a comment to posts
@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        comment_text = request.POST.get('comment_body')
        
        # If they actually typed something, save it to the database
        if comment_text:
            Comment.objects.create(post=post, author=request.user, body=comment_text)
            
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# Delete a comment (either your comment on someone's post, or someone else's comment on your post)
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.user == comment.author or request.user == comment.post.author:
        comment.delete()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def update_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        profile = request.user.profile
        profile.profile_picture = request.FILES['profile_pic']
        profile.save()
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/account/'))