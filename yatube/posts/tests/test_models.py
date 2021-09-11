from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test grp',
            slug='Test slug',
            description='Test desc',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
        )

    def test_post_str(self):
        """Test str for Post model"""
        post = PostModelTest.post
        self.assertEqual(str(post), post.text[:15],
                         'check post __str__ method')

    def test_group_str(self):
        """Test str for Group model"""
        group = PostModelTest.group
        self.assertEqual(str(group), group.title,
                         'check group __str__ method')
