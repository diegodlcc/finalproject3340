from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login

# This is the Homepage
def home(request):
    return render(request, 'index.html')

# Sports page
def sports(request):
    sports_events = [
        {
            'title': 'Intramural Soccer Tryouts',
            'date': 'April 25, 2026',
            'time': '6:00 PM - 8:00 PM',
            'location': 'UTRGV Field Complex',
            'description': 'Join fellow students for open tryouts and meet the intramural soccer community.'
        },
        {
            'title': 'Vaqueros Basketball Watch Party',
            'date': 'April 27, 2026',
            'time': '7:30 PM - 9:30 PM',
            'location': 'Student Union Theater',
            'description': 'Cheer on the Vaqueros with free snacks, giveaways, and student spirit.'
        },
        {
            'title': 'Campus 5K Fun Run',
            'date': 'May 1, 2026',
            'time': '7:00 AM - 9:00 AM',
            'location': 'Main Campus Loop',
            'description': 'A fun and active event for students of all experience levels. Walkers are welcome too.'
        },
    ]
    return render(request, 'sports.html', {'sports_events': sports_events})

# This is the Account Management page
def account(request):
    return render(request, 'account.html')

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
