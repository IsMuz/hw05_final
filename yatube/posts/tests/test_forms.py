from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm, CommentForm
from ..models import Group, Post, Comment

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            author=cls.user,
            text='test text',
            group=cls.group
        )
        # cls.comment = Comment.objects.create(
        #     text='test',
        #     author=cls.user,
        #     post=cls.post,
        # )
        cls.post_form = PostForm()
        cls.comment_form = CommentForm()

    def setUp(self):
        self.guest = Client()
        self.auth = Client()
        self.auth.force_login(self.user)

    def test_post_create(self):
        p_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test text',
            'group': self.group.id,
            'image': uploaded,
        }
        rev = reverse('posts:profile', args=[self.user.username])
        response = self.auth.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, rev)
        self.assertEqual(Post.objects.count(), p_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group']
            ).exists()
        )

    def test_post_edit(self):
        form_data = {
            'text': 'test text1',
        }
        self.auth.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=None
            ).exists()
        )

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

    def test_subscrition(self):
        pass
