from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import Event, RSVP
import datetime


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def make_officer(user):
    """Add a user to the club_officer group."""
    group, _ = Group.objects.get_or_create(name='club_officer')
    user.groups.add(group)


def make_event(user, **kwargs):
    """Create a test event with sensible defaults."""
    defaults = {
        'title': 'Test Event',
        'description': 'A test event.',
        'date': datetime.date.today() + datetime.timedelta(days=7),
        'time': datetime.time(14, 0),
        'location': 'UTRGV Main Campus',
        'category': 'academic',
        'capacity': 30,
        'created_by': user,
    }
    defaults.update(kwargs)
    return Event.objects.create(**defaults)


# ─────────────────────────────────────────────
# MODEL TESTS
# ─────────────────────────────────────────────

class EventModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='officer', password='pass1234')

    def test_event_str(self):
        event = make_event(self.user, title='Science Fair')
        self.assertEqual(str(event), 'Science Fair')

    def test_spots_left_full_capacity(self):
        event = make_event(self.user, capacity=3)
        self.assertEqual(event.spots_left(), 3)

    def test_spots_left_decreases_with_rsvps(self):
        event = make_event(self.user, capacity=3)
        attendee = User.objects.create_user(username='attendee', password='pass1234')
        RSVP.objects.create(event=event, user=attendee)
        self.assertEqual(event.spots_left(), 2)

    def test_spots_left_reaches_zero(self):
        event = make_event(self.user, capacity=1)
        RSVP.objects.create(event=event, user=self.user)
        self.assertEqual(event.spots_left(), 0)

    def test_event_ordering_by_date_then_time(self):
        today = datetime.date.today()
        e1 = make_event(self.user, title='Later', date=today + datetime.timedelta(days=5))
        e2 = make_event(self.user, title='Sooner', date=today + datetime.timedelta(days=2))
        events = list(Event.objects.all())
        self.assertEqual(events[0], e2)
        self.assertEqual(events[1], e1)

    def test_event_category_choices(self):
        for category, _ in Event.CATEGORY_CHOICES:
            event = make_event(self.user, category=category)
            self.assertEqual(event.category, category)


class RSVPModelTest(TestCase):

    def setUp(self):
        self.officer = User.objects.create_user(username='officer', password='pass1234')
        self.user = User.objects.create_user(username='student', password='pass1234')
        self.event = make_event(self.officer, capacity=10)

    def test_rsvp_str(self):
        rsvp = RSVP.objects.create(event=self.event, user=self.user)
        self.assertIn('student', str(rsvp))
        self.assertIn('Test Event', str(rsvp))

    def test_duplicate_rsvp_not_allowed(self):
        RSVP.objects.create(event=self.event, user=self.user)
        with self.assertRaises(Exception):
            RSVP.objects.create(event=self.event, user=self.user)

    def test_rsvp_unique_per_user_per_event(self):
        RSVP.objects.create(event=self.event, user=self.user)
        count = RSVP.objects.filter(event=self.event, user=self.user).count()
        self.assertEqual(count, 1)


# ─────────────────────────────────────────────
# VIEW TESTS — EVENT LIST
# ─────────────────────────────────────────────

class EventListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='officer', password='pass1234')

    def test_event_list_loads(self):
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_list.html')

    def test_event_list_shows_events(self):
        make_event(self.user, title='Campus Concert')
        response = self.client.get(reverse('event_list'))
        self.assertContains(response, 'Campus Concert')

    def test_event_list_category_filter(self):
        make_event(self.user, title='Academic Talk', category='academic')
        make_event(self.user, title='Soccer Game', category='sports')
        response = self.client.get(reverse('event_list') + '?category=academic')
        self.assertContains(response, 'Academic Talk')
        self.assertNotContains(response, 'Soccer Game')

    def test_event_list_accessible_to_anonymous(self):
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)


# ─────────────────────────────────────────────
# VIEW TESTS — EVENT DETAIL
# ─────────────────────────────────────────────

class EventDetailViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='officer', password='pass1234')
        self.event = make_event(self.user, title='Detail Test Event')

    def test_event_detail_loads(self):
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_detail.html')

    def test_event_detail_shows_title(self):
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertContains(response, 'Detail Test Event')

    def test_event_detail_404_for_nonexistent(self):
        response = self.client.get(reverse('event_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_rsvp_status_shown_for_authenticated_user(self):
        self.client.login(username='officer', password='pass1234')
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertIn('user_rsvpd', response.context)


# ─────────────────────────────────────────────
# VIEW TESTS — EVENT CREATE
# ─────────────────────────────────────────────

class EventCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.officer = User.objects.create_user(username='officer', password='pass1234')
        self.student = User.objects.create_user(username='student', password='pass1234')
        make_officer(self.officer)

    def test_officer_can_access_create_form(self):
        self.client.login(username='officer', password='pass1234')
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 200)

    def test_non_officer_redirected_from_create(self):
        self.client.login(username='student', password='pass1234')
        response = self.client.get(reverse('event_create'))
        self.assertRedirects(response, reverse('event_list'))

    def test_anonymous_user_redirected_from_create(self):
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 302)

    def test_officer_can_create_event(self):
        self.client.login(username='officer', password='pass1234')
        self.client.post(reverse('event_create'), {
            'title': 'New Event',
            'description': 'A great event',
            'date': '2099-12-01',
            'time': '15:00',
            'location': 'Room 101',
            'category': 'social',
            'capacity': 20,
        })
        self.assertTrue(Event.objects.filter(title='New Event').exists())

    def test_non_officer_cannot_create_event(self):
        self.client.login(username='student', password='pass1234')
        self.client.post(reverse('event_create'), {
            'title': 'Sneaky Event',
            'description': 'Should not exist',
            'date': '2099-12-01',
            'time': '15:00',
            'location': 'Room 101',
            'category': 'social',
            'capacity': 20,
        })
        self.assertFalse(Event.objects.filter(title='Sneaky Event').exists())


# ─────────────────────────────────────────────
# VIEW TESTS — EVENT EDIT & DELETE
# ─────────────────────────────────────────────

class EventEditDeleteViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user(username='creator', password='pass1234')
        self.other = User.objects.create_user(username='other', password='pass1234')
        self.event = make_event(self.creator, title='Editable Event')

    def test_creator_can_edit_event(self):
        self.client.login(username='creator', password='pass1234')
        self.client.post(reverse('event_edit', args=[self.event.id]), {
            'title': 'Updated Title',
            'description': 'New desc',
            'date': '2099-12-01',
            'time': '10:00',
            'location': 'New Room',
            'category': 'sports',
            'capacity': 25,
        })
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Title')

    def test_non_creator_cannot_edit_event(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.post(reverse('event_edit', args=[self.event.id]), {
            'title': 'Hacked Title',
        })
        self.assertEqual(response.status_code, 404)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Editable Event')

    def test_creator_can_delete_event(self):
        self.client.login(username='creator', password='pass1234')
        self.client.post(reverse('event_delete', args=[self.event.id]))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_non_creator_cannot_delete_event(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.post(reverse('event_delete', args=[self.event.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Event.objects.filter(id=self.event.id).exists())


# ─────────────────────────────────────────────
# VIEW TESTS — RSVP
# ─────────────────────────────────────────────

class RSVPViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.officer = User.objects.create_user(username='officer', password='pass1234')
        self.student = User.objects.create_user(username='student', password='pass1234')
        self.event = make_event(self.officer, capacity=2)

    def test_authenticated_user_can_rsvp(self):
        self.client.login(username='student', password='pass1234')
        self.client.post(reverse('event_rsvp', args=[self.event.id]))
        self.assertTrue(RSVP.objects.filter(event=self.event, user=self.student).exists())

    def test_anonymous_user_cannot_rsvp(self):
        response = self.client.post(reverse('event_rsvp', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RSVP.objects.filter(event=self.event).exists())

    def test_rsvp_when_full_does_not_create_rsvp(self):
        # Fill the event to capacity
        u1 = User.objects.create_user(username='u1', password='pass1234')
        u2 = User.objects.create_user(username='u2', password='pass1234')
        RSVP.objects.create(event=self.event, user=u1)
        RSVP.objects.create(event=self.event, user=u2)
        # Now student tries to RSVP
        self.client.login(username='student', password='pass1234')
        self.client.post(reverse('event_rsvp', args=[self.event.id]))
        self.assertFalse(RSVP.objects.filter(event=self.event, user=self.student).exists())

    def test_user_can_cancel_rsvp(self):
        RSVP.objects.create(event=self.event, user=self.student)
        self.client.login(username='student', password='pass1234')
        self.client.post(reverse('event_unrsvp', args=[self.event.id]))
        self.assertFalse(RSVP.objects.filter(event=self.event, user=self.student).exists())

    def test_duplicate_rsvp_via_get_or_create(self):
        """RSVPing twice should not create duplicate entries."""
        self.client.login(username='student', password='pass1234')
        self.client.post(reverse('event_rsvp', args=[self.event.id]))
        self.client.post(reverse('event_rsvp', args=[self.event.id]))
        count = RSVP.objects.filter(event=self.event, user=self.student).count()
        self.assertEqual(count, 1)