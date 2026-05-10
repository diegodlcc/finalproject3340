from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from .models import Post

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
    # Look in templates for account.html
    return render(request, 'account.html')

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