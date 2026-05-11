from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, Profile


class PostModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass1234')

    def test_post_creation(self):
        post = Post.objects.create(author=self.user, content='Hello campus!')
        self.assertEqual(post.content, 'Hello campus!')
        self.assertEqual(post.author, self.user)

    def test_post_str(self):
        post = Post.objects.create(author=self.user, content='Short post')
        self.assertIn('testuser', str(post))
        self.assertIn('Short post', str(post))

    def test_post_ordering_newest_first(self):
        post1 = Post.objects.create(author=self.user, content='First post')
        post2 = Post.objects.create(author=self.user, content='Second post')
        posts = list(Post.objects.all())
        self.assertEqual(posts[0], post2)  # Newest first
        self.assertEqual(posts[1], post1)

    def test_post_max_length(self):
        long_content = 'x' * 160
        post = Post.objects.create(author=self.user, content=long_content)
        self.assertEqual(len(post.content), 160)


class ProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='pass1234')

    def test_profile_auto_created_on_user_creation(self):
        """Profile should be auto-created via signal when a User is created."""
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_str(self):
        profile = self.user.profile
        self.assertIn('profileuser', str(profile))
        self.assertIn('profile', str(profile))

    def test_profile_defaults(self):
        profile = self.user.profile
        self.assertEqual(profile.avatar_url, '')
        self.assertEqual(profile.bio, '')

    def test_get_avatar_returns_url_when_set(self):
        profile = self.user.profile
        profile.avatar_url = 'https://example.com/pic.jpg'
        profile.save()
        self.assertEqual(profile.get_avatar(), 'https://example.com/pic.jpg')

    def test_get_avatar_returns_none_when_not_set(self):
        profile = self.user.profile
        self.assertIsNone(profile.get_avatar())

    def test_profile_one_to_one_with_user(self):
        """Each user should have exactly one profile."""
        profile_count = Profile.objects.filter(user=self.user).count()
        self.assertEqual(profile_count, 1)


# ─────────────────────────────────────────────
# VIEW TESTS — HOME
# ─────────────────────────────────────────────

class HomeViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='homeuser', password='pass1234')

    def test_home_loads_for_anonymous_user(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_home_shows_posts(self):
        Post.objects.create(author=self.user, content='Visible post')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Visible post')

    def test_authenticated_user_can_create_post(self):
        self.client.login(username='homeuser', password='pass1234')
        response = self.client.post(reverse('home'), {'tweet_content': 'New post!'})
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(Post.objects.filter(content='New post!').exists())

    def test_anonymous_post_redirects_to_login(self):
        response = self.client.post(reverse('home'), {'tweet_content': 'Should not post'})
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(Post.objects.filter(content='Should not post').exists())

    def test_empty_post_content_not_saved(self):
        self.client.login(username='homeuser', password='pass1234')
        self.client.post(reverse('home'), {'tweet_content': '   '})
        self.assertEqual(Post.objects.count(), 0)


# ─────────────────────────────────────────────
# VIEW TESTS — POST CRUD
# ─────────────────────────────────────────────

class DeletePostViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username='author', password='pass1234')
        self.other = User.objects.create_user(username='other', password='pass1234')
        self.post = Post.objects.create(author=self.author, content='To be deleted')

    def test_author_can_delete_post(self):
        self.client.login(username='author', password='pass1234')
        response = self.client.post(reverse('delete_post', args=[self.post.id]))
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_non_author_cannot_delete_post(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.post(reverse('delete_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_anonymous_delete_redirects_to_login(self):
        response = self.client.post(reverse('delete_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())


class EditPostViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username='author', password='pass1234')
        self.other = User.objects.create_user(username='other', password='pass1234')
        self.post = Post.objects.create(author=self.author, content='Original content')

    def test_author_can_edit_post(self):
        self.client.login(username='author', password='pass1234')
        self.client.post(reverse('edit_post', args=[self.post.id]), {'content': 'Updated!'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'Updated!')

    def test_non_author_cannot_edit_post(self):
        self.client.login(username='other', password='pass1234')
        response = self.client.post(reverse('edit_post', args=[self.post.id]), {'content': 'Hacked!'})
        self.assertEqual(response.status_code, 404)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'Original content')

    def test_edit_with_empty_content_does_not_save(self):
        self.client.login(username='author', password='pass1234')
        self.client.post(reverse('edit_post', args=[self.post.id]), {'content': '   '})
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'Original content')


# ─────────────────────────────────────────────
# VIEW TESTS — ACCOUNT
# ─────────────────────────────────────────────

class AccountViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='accountuser', password='pass1234', email='old@test.com'
        )

    def test_account_page_requires_login(self):
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)

    def test_account_page_loads_for_logged_in_user(self):
        self.client.login(username='accountuser', password='pass1234')
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

    def test_update_info(self):
        self.client.login(username='accountuser', password='pass1234')
        self.client.post(reverse('account'), {
            'action': 'update_info',
            'username': 'newname',
            'email': 'new@test.com',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newname')
        self.assertEqual(self.user.email, 'new@test.com')

    def test_update_avatar_and_bio(self):
        self.client.login(username='accountuser', password='pass1234')
        self.client.post(reverse('account'), {
            'action': 'update_avatar',
            'avatar_url': 'https://example.com/pic.jpg',
            'bio': 'Go Vaqueros!',
        })
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.avatar_url, 'https://example.com/pic.jpg')
        self.assertEqual(self.user.profile.bio, 'Go Vaqueros!')

    def test_change_password_valid(self):
        self.client.login(username='accountuser', password='pass1234')
        response = self.client.post(reverse('account'), {
            'action': 'change_password',
            'old_password': 'pass1234',
            'new_password1': 'NewSecure@99',
            'new_password2': 'NewSecure@99',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecure@99'))

    def test_change_password_invalid_shows_error(self):
        self.client.login(username='accountuser', password='pass1234')
        response = self.client.post(reverse('account'), {
            'action': 'change_password',
            'old_password': 'pass1234',
            'new_password1': 'NewSecure@99',
            'new_password2': 'DoesNotMatch',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('pass1234'))  # Unchanged


# ─────────────────────────────────────────────
# VIEW TESTS — SIGNUP
# ─────────────────────────────────────────────

class SignupViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_signup_page_loads(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_valid_signup_creates_user_and_redirects(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newvaquero',
            'password1': 'StrongPass@1',
            'password2': 'StrongPass@1',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='newvaquero').exists())

    def test_valid_signup_auto_creates_profile(self):
        self.client.post(reverse('signup'), {
            'username': 'newvaquero',
            'password1': 'StrongPass@1',
            'password2': 'StrongPass@1',
        })
        user = User.objects.get(username='newvaquero')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_invalid_signup_does_not_create_user(self):
        self.client.post(reverse('signup'), {
            'username': 'baduser',
            'password1': 'pass',
            'password2': 'different',
        })
        self.assertFalse(User.objects.filter(username='baduser').exists())