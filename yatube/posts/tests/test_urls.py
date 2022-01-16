from copy import deepcopy
from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class UrlsTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user_author = User.objects.create(username='Author')
        cls.client_author = Client()
        cls.client_author.force_login(UrlsTestCase.user_author)

        cls.user_not_author = User.objects.create(username='NotAuthor')
        cls.client_not_author = Client()
        cls.client_not_author.force_login(UrlsTestCase.user_not_author)

        cls.client_guest = Client()
        cls.client_list = [cls.client_author,
                           cls.client_not_author,
                           cls.client_guest]

        cls.group = Group.objects.create(
            title='test group',
            slug='test_slug',)

        cls.post = Post.objects.create(
            text='test_text',
            author=cls.user_author,
            group=cls.group,)

        cls.author_routes_status_code = {
            '/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
            f'/group/{cls.group.slug}/': HTTPStatus.OK,
            f'/profile/{cls.user_author.username}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/comment/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/edit/': HTTPStatus.OK,
            f'profile/{cls.user_not_author}/follow/': HTTPStatus.NOT_FOUND,
            f'profile/{cls.user_not_author}/unfollow/': HTTPStatus.NOT_FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }

        cls.not_author_routes_status_code = deepcopy(
            cls.author_routes_status_code)
        cls.not_author_routes_status_code[
            f'/posts/{cls.post.id}/edit/'] = HTTPStatus.FOUND
        cls.not_author_routes_status_code[
            f'profile/{cls.user_not_author}/follow/'] = HTTPStatus.NOT_FOUND

        cls.guest_routes_status_code = deepcopy(
            cls.author_routes_status_code)
        cls.guest_routes_status_code[
            f'/posts/{cls.post.id}/edit/'] = HTTPStatus.FOUND
        cls.guest_routes_status_code['/create/'] = HTTPStatus.FOUND
        cls.guest_routes_status_code[
            f'/posts/{cls.post.id}/comment/'] = HTTPStatus.FOUND
        cls.guest_routes_status_code['/follow/'] = HTTPStatus.FOUND

        cls.routes_status_code_list = [
            cls.author_routes_status_code,
            cls.not_author_routes_status_code,
            cls.guest_routes_status_code]

        cls.client_routes_tuple = zip(
            cls.client_list, cls.routes_status_code_list)

        cls.pages_attributes = {
            'index': {'url': '/',
                      'template': 'posts/index.html', },
            'follow_index': {'url': '/follow/',
                             'template': 'posts/follow_index.html', },
            'group_list': {'url': f'/group/{cls.group.slug}/',
                           'template': 'posts/group_list.html', },
            'profile': {'url': f'/profile/{cls.user_author.username}/',
                        'template': 'posts/profile.html', },
            'post_detail': {'url': f'/posts/{cls.post.id}/',
                            'template': 'posts/post_detail.html', },
            'post_create': {'url': '/create/',
                            'template': 'posts/create_post.html', },
            'post_edit': {'url': f'/posts/{cls.post.id}/edit/',
                          'template': 'posts/create_post.html', },
        }

    def test_rout_uses_correct_template(self):
        """Tests that the pages match the templates"""
        client = self.client_author
        for name, attribute in UrlsTestCase.pages_attributes.items():
            with self.subTest(name=name):
                response = client.get(attribute['url'])
                self.assertTemplateUsed(response, attribute['template'])

    def test_users_return_correct_status_code(self):
        """Tests that response status codes match users access rights"""
        for client, routes in UrlsTestCase.client_routes_tuple:
            for rout, status_code in routes.items():
                with self.subTest(rout=rout, client=client):
                    response = client.get(rout)
                    self.assertEqual(response.status_code, status_code)
