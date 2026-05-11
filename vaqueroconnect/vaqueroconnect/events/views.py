from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event, RSVP

def is_club_officer(user):
    return user.groups.filter(name='club_officer').exists()

# List all events (with optional category filter)
def event_list(request):
    category = request.GET.get('category')
    events = Event.objects.all()
    if category:
        events = events.filter(category=category)
    return render(request, 'events/event_list.html', {
        'events': events,
        'selected_category': category,
    })

# View a single event
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user_rsvpd = False
    if request.user.is_authenticated:
        user_rsvpd = RSVP.objects.filter(event=event, user=request.user).exists()
    return render(request, 'events/event_detail.html', {
        'event': event,
        'user_rsvpd': user_rsvpd,
    })

# Create an event (club officers only)
@login_required
def event_create(request):
    if not is_club_officer(request.user):
        return redirect('event_list')
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date = request.POST.get('date')
        time = request.POST.get('time')
        location = request.POST.get('location')
        category = request.POST.get('category')
        capacity = request.POST.get('capacity', 50)
        Event.objects.create(
            title=title, description=description, date=date,
            time=time, location=location, category=category,
            capacity=capacity, created_by=request.user
        )
        return redirect('event_list')
    return render(request, 'events/event_form.html', {'action': 'Create'})

# Edit an event (creator only)
@login_required
def event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.description = request.POST.get('description')
        event.date = request.POST.get('date')
        event.time = request.POST.get('time')
        event.location = request.POST.get('location')
        event.category = request.POST.get('category')
        event.capacity = request.POST.get('capacity', 50)
        event.save()
        return redirect('event_detail', event_id=event.id)
    return render(request, 'events/event_form.html', {'action': 'Edit', 'event': event})

# Delete an event (creator only)
@login_required
def event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    if request.method == 'POST':
        event.delete()
    return redirect('event_list')

# RSVP to an event
@login_required
def event_rsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        if event.spots_left() > 0:
            RSVP.objects.get_or_create(event=event, user=request.user)
    return redirect('event_detail', event_id=event.id)

# Cancel RSVP
@login_required
def event_unrsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        RSVP.objects.filter(event=event, user=request.user).delete()
    return redirect('event_detail', event_id=event.id)