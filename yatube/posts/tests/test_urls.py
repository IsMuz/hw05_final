from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.user1 = User.objects.create_user(username='test1')
        cls.group = Group.objects.create(
            title='test-grp',
            slug='test-slug',
            description='test desc',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test text',
        )

    def setUp(self):
        self.guest = Client()
        self.auth = Client()
        self.auth.force_login(self.user)

    def test_urls_location_guest(self):
        """Pages accessed by guest user"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, _template, in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK, f'{address}')

    def test_urls_location_auth(self):
        """Pages accessed only by authorized user"""
        response = self.auth.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_urls_correct_templates(self):
        """URLs use right templates"""
        cache.clear()
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/post_create.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.auth.get(address)
                self.assertTemplateUsed(response, template, f'{address}')
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_random(self):
        """Unknown page returns 404"""
        response = self.guest.get('/random_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_edit_post_redirect_guest(self):
        response = self.guest.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response,
                             '/auth/login/?next=%2Fposts%2F1%2Fedit%2F')

    def test_edit_post_redirect_not_author(self):
        self.auth.force_login(self.user1)
        response = self.auth.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response,
                             f'/posts/{self.post.id}/')
