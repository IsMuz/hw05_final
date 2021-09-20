from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, Follow

User = get_user_model()


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
            name='small.gif',
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
            image=cls.uploaded,
        )



    def setUp(self):
        self.guest = Client()
        self.auth = Client()
        self.auth.force_login(self.user)
        for i in range(15):
            Post.objects.create(
                text=f'test text {i}',
                author=self.user,
                group=self.group,
                image=self.uploaded,
            )

    def test_pages_uses_correct_template(self):
        """Urls use right templates"""
        templates_page_names = {
            # reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:group',
                    args=[self.group.slug]): 'posts/group_list.html',
            reverse('posts:profile',
                    args=[self.user.username]): 'posts/profile.html',
            reverse('posts:post_detail',
                    args=[self.post.id]): 'posts/post_detail.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.auth.get(reverse_name)
                self.assertTemplateUsed(response, template, f'{reverse_name}')

    def test_index_context(self):
        """Template index generated with right context"""
        response = self.auth.get(reverse('posts:index') + '?page=2')
        f_obj = response.context['page_obj'][5]
        self.assert_equal_context(f_obj)

    def test_group_list_context(self):
        """Template group_list generated with right context"""
        response = self.auth.get(reverse('posts:group',
                                         args=[self.group.slug]))
        s_obj = response.context['page_obj'][0]
        self.assert_equal_context(s_obj)
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
        self.assert_equal_context(s_obj)
        self.assertEqual(response.context['author'].username,
                         self.user.username)
        self.assertEqual(response.context['author'].first_name,
                         self.user.first_name)

    def test_post_detail_context(self):
        response = self.auth.get(reverse('posts:post_detail',
                                         args=[self.post.id]))
        self.assertEqual(response.context['post'].text,
                         self.post.text)
        self.assertEqual(response.context['post'].author.username,
                         self.post.author.username)
        self.assertEqual(response.context['post'].group.title,
                         self.post.group.title)

    def test_index_fpage_paginator(self):
        response = self.auth.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_spage_paginator(self):
        response = self.auth.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 6, f'{response}')

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
        self.auth.post(
            reverse('posts:profile_follow', args=[self.user1.username]),
            follow=True,
        )
        self.auth.post(
            reverse('posts:profile_unfollow', args=[self.user1.username]),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), c_count)

    def assert_equal_context(self, obj):
        post_text = obj.text
        post_author = obj.author.username
        post_group = obj.group.title
        post_image = obj.image
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.post.author.username)
        self.assertEqual(post_group, self.post.group.title)
        self.assertEqual(post_image, self.post.image)
