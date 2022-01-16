import shutil
import tempfile

from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User
from yatube.settings import BASE_DIR, PAGINATOR_NUM_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user_author = User.objects.create(username='Author')
        cls.client_author = Client()
        cls.client_author.force_login(cls.user_author)

        cls.user_not_author = User.objects.create(username='NotAuthor')
        cls.client_not_author = Client()
        cls.client_not_author.force_login(cls.user_not_author)

        cls.client_guest = Client()

        cls.group = Group.objects.create(
            title='test group',
            slug='test_slug',)
        cls.group_another = Group.objects.create(
            title='another test group',
            slug='another_slug',)

        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_image = SimpleUploadedFile(
            name='test_image.gif',
            content=cls.image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='0123456789ABCDEF',
            author=cls.user_author,
            group=cls.group,
            image=cls.uploaded_image,
        )

        cls.pages_attributes = {
            'index': {'reversed_name': reverse(
                'posts:index'),
                'template': 'posts/index.html', },
            'group_list': {'reversed_name': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}),
                'template': 'posts/group_list.html', },
            'profile': {'reversed_name': reverse(
                'posts:profile',
                kwargs={'username': cls.user_author.username}),
                'template': 'posts/profile.html', },
            'post_detail': {'reversed_name': reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}),
                'template': 'posts/post_detail.html', },
            'post_create': {'reversed_name': reverse(
                'posts:post_create'),
                'template': 'posts/create_post.html', },
            'post_edit': {'reversed_name': reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}),
                'template': 'posts/create_post.html', },
            'follow_index': {'reversed_name': reverse(
                'posts:follow_index'),
                'template': 'posts/follow_index.html', }
        }

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def _get_response_run_contex_tests(self, page_name):
        """return the response object and performs a contextual correctness."""
        client = ViewsTestCase.client_author
        response = client.get(
            ViewsTestCase.pages_attributes[page_name]['reversed_name']
        )
        try:
            first_post = response.context['page_obj'][0]
        except KeyError:
            first_post = response.context['post']
        self.assertEqual(first_post.text, ViewsTestCase.post.text)
        self.assertEqual(first_post.author, ViewsTestCase.user_author)
        self.assertEqual(first_post.group, ViewsTestCase.group)
        self.assertEqual(first_post.image, ViewsTestCase.post.image)
        return response

    def test_reversed_name_uses_correct_template(self):
        """view functions uses right templates."""
        client = ViewsTestCase.client_author
        for name, attribute in ViewsTestCase.pages_attributes.items():
            with self.subTest(name=name):
                response = client.get(attribute['reversed_name'])
                self.assertTemplateUsed(response, attribute['template'])

    def test_paginator(self):
        """Paginator on page 'index', 'group_list', 'profile' work correct."""
        client = ViewsTestCase.client_not_author
        client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': ViewsTestCase.user_author.username}
        ))
        tests_views = 'index', 'group_list', 'profile', 'follow_index'
        posts_list = [
            Post(
                text=f'Post {num}',
                author=ViewsTestCase.user_author,
                group=ViewsTestCase.group,
            ) for num in range(1, 16)
        ]
        Post.objects.bulk_create(posts_list)
        LAST_PAGE_AMOUNT = Post.objects.count() % PAGINATOR_NUM_PAGE
        pages = {1: PAGINATOR_NUM_PAGE,
                 2: LAST_PAGE_AMOUNT, }
        for name in tests_views:
            for page, count in pages.items():
                with self.subTest(name=name):
                    response = client.get(
                        ViewsTestCase.pages_attributes[name]['reversed_name'],
                        {'page': page})
                    self.assertEqual(len(response.context['page_obj']), count)

    def test_index_page_show_correct_context(self):
        """The home template is formed with the right context."""
        ViewsTestCase._get_response_run_contex_tests(self, 'index')

    def test_group_list_page_return_correct_context(self):
        """The home template is formed with the right context."""
        response = ViewsTestCase._get_response_run_contex_tests(
            self, 'group_list')
        for post in response.context['page_obj']:
            self.assertEqual(post.group, ViewsTestCase.group)

    def test_profile_page_return_correct_context(self):
        """The profile template is formed with the right context"""
        response = ViewsTestCase._get_response_run_contex_tests(
            self, 'profile')
        author = ViewsTestCase.user_author
        context = response.context['page_obj'][:PAGINATOR_NUM_PAGE]
        expected_context = [
            x for x in Post.objects.filter(author=author)[:PAGINATOR_NUM_PAGE]]
        self.assertEqual(context, expected_context)

    def test_post_detail_page_return_correct_context(self):
        """The post_detail template is formed with the right post"""
        ViewsTestCase._get_response_run_contex_tests(self, 'post_detail')

    def test_post_create_page_return_correct_context(self):
        """The create page template is formed with the right form"""
        client = ViewsTestCase.client_author
        expected_form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField, }
        response = client.get(
            ViewsTestCase.pages_attributes['post_create']['reversed_name'])
        for name, field in expected_form.items():
            with self.subTest(name=name):
                expected_field = response.context['form'].fields.get(name)
                self.assertIsInstance(expected_field, field)

    def test_post_edit_page_return_correct_context(self):
        """The post edit template is formed with the right form"""
        client = ViewsTestCase.client_author
        expected_form = {'text': forms.fields.CharField,
                         'group': forms.fields.ChoiceField, }
        response = client.get(
            ViewsTestCase.pages_attributes['post_edit']['reversed_name'])
        for name, field in expected_form.items():
            with self.subTest(name=name):
                expected_field = response.context['form'].fields.get(name)
                self.assertIsInstance(expected_field, field)

    def test_created_post_added_on_correct_pages(self):
        """Checks that the created post appears on the correct pages
        and not on others"""
        client = ViewsTestCase.client_author
        new_post = Post.objects.create(
            text='test post',
            group=ViewsTestCase.group,
            author=ViewsTestCase.user_author,)
        response_index = client.get(
            ViewsTestCase.pages_attributes['profile']['reversed_name'])
        response_group = client.get(
            ViewsTestCase.pages_attributes['group_list']['reversed_name'])
        response_another_group = client.get(
            reverse('posts:group_list',
                    kwargs={'slug': ViewsTestCase.group_another.slug}))
        response_profile = client.get(
            ViewsTestCase.pages_attributes['profile']['reversed_name'])
        self.assertIn(new_post, response_index.context['page_obj'])
        self.assertIn(new_post, response_group.context['page_obj'])
        self.assertNotIn(new_post, response_another_group.context['page_obj'])
        self.assertIn(new_post, response_profile.context['page_obj'])
        Post.objects.filter(
            text=new_post.text,
            group=ViewsTestCase.group,
            author=ViewsTestCase.user_author).delete()

    def test_cache_on_index_page(self):
        """Test the cache on index page"""
        client = ViewsTestCase.client_author
        response_first = client.get(
            ViewsTestCase.pages_attributes['index']['reversed_name']
        )
        content_first = response_first.content
        test_post = Post.objects.create(
            text='test_cache_post',
            author=ViewsTestCase.user_author,)
        response_second = client.get(
            ViewsTestCase.pages_attributes['index']['reversed_name']
        )
        content_second = response_second.content
        self.assertEqual(content_first, content_second, '<Page is not cached>')
        cache.clear()
        response_third = client.get(
            ViewsTestCase.pages_attributes['index']['reversed_name']
        )
        self.assertIn(test_post,
                      response_third.context['page_obj'],
                      '<Post was not added in cotext>', )


class FollowTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='Author')
        cls.client_user_author = Client()
        cls.client_user_author.force_login(FollowTestCase.user_author)

        cls.user_second = User.objects.create(username='Second')
        cls.client_user_second = Client()
        cls.client_user_second.force_login(FollowTestCase.user_second)

        cls.user_third = User.objects.create(username='Third')
        cls.client_user_third = Client()
        cls.client_user_third.force_login(FollowTestCase.user_third)

    def test_authorized_user_can_follow(self):
        """Test this user can subscribe for other users."""
        FollowTestCase.client_user_second.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowTestCase.user_author.username}
        ))
        self.assertTrue(Follow.objects.filter(
            user=FollowTestCase.user_second,
            author=FollowTestCase.user_author
        ).exists())

    def test_authorized_user_can_unfollow(self):
        """Test this user can unsubscribe/"""
        Follow.objects.create(user=FollowTestCase.user_second,
                              author=FollowTestCase.user_author)
        FollowTestCase.client_user_second.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': FollowTestCase.user_author.username}
        ))
        self.assertFalse(Follow.objects.filter(
            user=FollowTestCase.user_second,
            author=FollowTestCase.user_author
        ).exists())

    def test_follow_index_page_shows_correct_context(self):
        """The follow_index template is formed with the right context."""
        Follow.objects.create(user=FollowTestCase.user_second,
                              author=FollowTestCase.user_author)
        post_user_author = Post.objects.create(
            text='Test_post_author',
            author=FollowTestCase.user_author, )
        response = FollowTestCase.client_user_second.get(
            reverse('posts:follow_index')
        )
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, post_user_author.text)
        self.assertEqual(first_post.author, FollowTestCase.user_author)
        self.assertIn(post_user_author, response.context['page_obj'])

    def test_follow_index_page_didnt_shows_uncorrect_context(self):
        """The follow_index template uninclude unfollow authors posts."""
        Follow.objects.create(user=FollowTestCase.user_author,
                              author=FollowTestCase.user_third)
        Follow.objects.create(user=FollowTestCase.user_second,
                              author=FollowTestCase.user_author)
        Follow.objects.create(user=FollowTestCase.user_third,
                              author=FollowTestCase.user_second)
        post_user_author = Post.objects.create(
            text='Test_post_author',
            author=FollowTestCase.user_author, )
        post_user_second = Post.objects.create(
            text='Test_post_from_second_user',
            author=FollowTestCase.user_second, )
        post_user_third = Post.objects.create(
            text='Test_post_from_third_user',
            author=FollowTestCase.user_third, )
        test_posts = post_user_author, post_user_second, post_user_third
        expected_posts_for_clients = {
            FollowTestCase.client_user_author: post_user_third,
            FollowTestCase.client_user_second: post_user_author,
            FollowTestCase.client_user_third: post_user_second, }
        for user, expected_post in expected_posts_for_clients.items():
            response = user.get(reverse('posts:follow_index'))
            for post in (i for i in test_posts if i != expected_post):
                with self.subTest(user=user, post=post):
                    self.assertNotIn(post, response.context['page_obj'])
