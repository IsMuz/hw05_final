from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_static(self):
        urls = [
            '/', '/about/author/', '/about/tech/'
        ]
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)


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
        self.auth1 = Client()
        self.auth.force_login(self.user)
        self.auth.force_login(self.user1)

    def test_urls_location_guest(self):
        """Pages accessed by guest user"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, template, in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_urls_location_auth(self):
        """Pages accessed only by authorized user"""
        templates_url_names = {
            '/create/',
            # f'/posts/{self.post.id}/edit/',
        }
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.auth.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_urls_correct_templates(self):
        """URLs use right templates"""
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/post_create.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            # f'/posts/{self.post.id}/edit/': 'posts/post_create.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.auth.get(address)
                self.assertTemplateUsed(response, template)

    def test_random(self):
        """Unknown page returns 404"""
        response = self.guest.get('/random_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_edit_post_redirect_guest(self):
        response = self.guest.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, '/auth/login/?next=%2Fposts%2F1%2Fedit%2F')

    def test_edit_post_redirect_not_author(self):
        response = self.auth1.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, '/auth/login/?next=%2Fposts%2F1%2Fedit%2F')

    def test_edit_post_redirect_auth(self):
        response = self.auth.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')



