import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Follow, Comment

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(
            username='auth',
            first_name='leo'
        )
        cls.user1 = User.objects.create_user(
            username='auth1',
            first_name='leo1'
        )
        cls.group = Group.objects.create(
            title='test grp',
            slug='test-slug',
            description='test desc',
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest = Client()
        self.auth = Client()
        self.auth.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Urls use right templates"""
        cache.clear()
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:group',
                    args=[self.group.slug]): 'posts/group_list.html',
            reverse('posts:profile',
                    args=[self.user.username]): 'posts/profile.html',
            reverse('posts:post_detail',
                    args=[self.post.id]): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    args=[self.post.id]): 'posts/post_create.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.auth.get(reverse_name)
                self.assertTemplateUsed(response, template, f'{reverse_name}')

    def test_index_context(self):
        """Template index generated with right context"""
        cache.clear()
        response = self.auth.get(reverse('posts:index'))
        f_obj = response.context['page_obj'][0]
        self.assert_post_context(f_obj)

    def test_group_list_context(self):
        """Template group_list generated with right context"""
        response = self.auth.get(reverse('posts:group',
                                         args=[self.group.slug]))
        s_obj = response.context['page_obj'][0]
        self.assert_post_context(s_obj)
        self.assertEqual(response.context['group'].title,
                         self.group.title)
        self.assertEqual(response.context['group'].slug,
                         self.group.slug)
        self.assertEqual(response.context['group'].description,
                         self.group.description)

    def test_profile_context(self):
        response = self.auth.get(reverse('posts:profile',
                                         args=[self.user.username]))
        s_obj = response.context['page_obj'][0]
        self.assert_post_context(s_obj)
        self.assertEqual(response.context['author'].username,
                         self.user.username)
        self.assertEqual(response.context['author'].first_name,
                         self.user.first_name)

    def test_post_detail_context(self):
        response = self.auth.get(reverse('posts:post_detail',
                                         args=[self.post.id]))
        self.assert_post_context(response.context['post'])

    def test_post_comment(self):
        c_count = Comment.objects.count()
        form_data = {
            'text': 'test1',
        }
        self.auth.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), c_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_post_edit_context(self):
        response = self.auth.get(reverse('posts:post_edit',
                                         args=[self.post.id]))
        self.assert_post_context(response.context['post'])

    def test_post_follow_user(self):
        cache.clear()
        Follow.objects.create(
            user=self.user1,
            author=self.user
        )
        self.auth.force_login(self.user1)
        response = self.auth.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_cache_index(self):
        response_before = self.auth.get(reverse('posts:index')).content
        Post.objects.create(
            author=self.user,
            text='test',
        )
        response_after = self.auth.get(reverse('posts:index')).content
        self.assertEqual(response_before, response_after)

    def test_post_list_wrong_group(self):
        group1 = Group.objects.create(
            title='test grp1',
            slug='test-slug1',
            description='test desc',
        )
        response = self.auth.get(reverse('posts:group',
                                         args=[group1.slug]))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_index_paginator(self):
        cache.clear()
        bulk_list = list()
        for i in range(15):
            bulk_list.append(Post(text=f'test {i}', author=self.user))
        Post.objects.bulk_create(bulk_list)
        response = self.auth.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.auth.get(reverse('posts:index')
                                 + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_sub(self):
        c_count = Follow.objects.count()
        self.auth.post(
            reverse('posts:profile_follow', args=[self.user1.username]),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), c_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user1
            ).exists()
        )

    def test_unsub(self):
        c_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user,
            author=self.user1
        )
        self.auth.post(
            reverse('posts:profile_unfollow', args=[self.user1.username]),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), c_count)

    def assert_post_context(self, obj):
        self.assertEqual(obj.text, self.post.text)
        self.assertEqual(obj.author.username, self.post.author.username)
        self.assertEqual(obj.group.title, self.post.group.title)
        self.assertEqual(obj.image, self.post.image)
