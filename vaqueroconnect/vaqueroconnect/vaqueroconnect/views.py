from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login as auth_login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Profile

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
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Update username and email
        if action == 'update_info':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            if username:
                request.user.username = username
            request.user.email = email
            request.user.save()
            messages.success(request, 'Profile updated successfully!')

        # Update avatar URL and bio
        elif action == 'update_avatar':
            avatar_url = request.POST.get('avatar_url', '').strip()
            bio = request.POST.get('bio', '').strip()
            profile.avatar_url = avatar_url
            profile.bio = bio
            profile.save()
            messages.success(request, 'Avatar updated successfully!')

        # Change password
        elif action == 'change_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
            else:
                messages.error(request, 'Please fix the errors below.')
                return render(request, 'account.html', {'password_form': form, 'profile': profile})

        return redirect('account')

    password_form = PasswordChangeForm(request.user)
    return render(request, 'account.html', {'password_form': password_form, 'profile': profile})

# This is account creation
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
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