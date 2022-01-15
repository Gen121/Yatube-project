import time
from django.test import TestCase

from posts.models import Group, Post, User


class ModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self) -> None:
        time.sleep(0.02)
        self.post_2 = Post.objects.create(
            author=ModelTestCase.user,
            text='abcdefghijklmnopqrstuvwxyz',
        )

    def test_post_model_repr_correct_name(self):
        """Check that Post model method __str__ work correctly"""
        REPRESENT_CHAR_NUM = 15
        repr_texts = (self.post_2.text[:REPRESENT_CHAR_NUM],
                      ModelTestCase.post.text[:REPRESENT_CHAR_NUM],)
        for post, repr_text in zip(Post.objects.all(), repr_texts):
            with self.subTest(post=post):
                self.assertEqual(post.__str__(), repr_text)

    def test_group_model_repr_correct_name(self):
        """Check that Post model method __str__ represent right num of char"""
        group = ModelTestCase.group
        self.assertEqual(group.__str__(), ModelTestCase.group.title)
