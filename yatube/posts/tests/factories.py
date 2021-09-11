import factory
from django.contrib.auth import get_user_model

from .. import models

User = get_user_model()


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Group

    title = 'test title'
    slug = 'test-slug'
    description = 'test desc'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Post

    text = factory.Sequence(lambda n: 'test%s' % n)
    group = factory.SubFactory(GroupFactory)
    author = factory.SubFactory(UserFactory)
