from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required

# This is the Homepage
@login_required
def account(request):
    # Look in templates for account.html
    return render(request, 'account.html') 

def home(request):
    # Look in templates folder for index.html (Homepage)
    return render(request, 'index.html')

# This is the Login page (dont need anymore since we're using Django's login view)
#def login(request):
#    # Look in templates for login.html 
#    return render(request, "login.html")

# This is the Account Management page
def account(request):
    # Look in templates for account.html
    return render(request, 'account.html')

#This is account creation
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