import shutil
import tempfile
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls.base import reverse

from posts.models import Comment, Group, Post, User
from yatube.settings import BASE_DIR

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user_author = User.objects.create(username='Author')
        cls.client_author = Client()
        cls.client_author.force_login(cls.user_author)

        cls.client_guest = Client()

        cls.group = Group.objects.create(
            title='test group',
            slug='test_slug',)
        cls.group_another = Group.objects.create(
            title='test another',
            slug='test_another',)

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
            content=FormTestCase.image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='0123456789ABCDEF',
            author=cls.user_author,
            group=cls.group,
        )

        cls.form_data = {
            'text': 'new_post',
            'group': cls.group.id,
            'image': cls.uploaded_image,
        }

        cls.page_reversed_name = {
            'post_create': reverse('posts:post_create'),
            'post_edit': reverse('posts:post_edit',
                                 kwargs={'post_id': cls.post.pk}),
            'post_detail': reverse('posts:post_detail',
                                   kwargs={'post_id': cls.post.pk}),
            'profile': reverse('posts:profile',
                               kwargs={'username': cls.user_author.username}),
            'login': reverse('users:login'),
            'add_comment': reverse('posts:add_comment',
                                   kwargs={"post_id": cls.post.pk}),
        }

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_authentificated_created_page_work_correctly(self):
        """The post created from the form on the "/create/" page was added
        to the db, the client was redirected to the "profile" page"""
        page = FormTestCase.page_reversed_name['post_create']
        page_redirect = FormTestCase.page_reversed_name['profile']
        client = FormTestCase.client_author
        image_uploaded_route = Post.image.field.upload_to
        response = client.post(page, data=FormTestCase.form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, page_redirect)
        new_post = Post.objects.latest('pub_date')
        expected_new_post_atributes = {
            'author': FormTestCase.user_author,
            'group_id': FormTestCase.form_data['group'],
            'text': FormTestCase.form_data['text'],
            'image': image_uploaded_route + FormTestCase.uploaded_image.name,
        }
        for field, val in expected_new_post_atributes.items():
            with self.subTest(field=field):
                self.assertEqual(new_post.__getattribute__(field), val)

    def test_guests_created_page_work_correctly(self):
        """The "/create/" page make redirect unauth client on "/login/" page,
        post was not added to the db"""
        page = FormTestCase.page_reversed_name['post_create']
        pages_redirect = (FormTestCase.page_reversed_name['login'],
                          FormTestCase.page_reversed_name['post_create'])
        client = FormTestCase.client_guest
        posts_count = Post.objects.count()
        group_id = FormTestCase.group_another.id
        form_data = {'text': 'impossible_post', 'group': group_id, }
        response = client.post(page, data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, '?next='.join(pages_redirect))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_page_work_correctly(self):
        """The post being edited by form on the "post_edit" page has been
        changed in the db, the client has been redirected to the "post_detail"
        page"""
        page = FormTestCase.page_reversed_name['post_edit']
        page_redirect = FormTestCase.page_reversed_name['post_detail']
        client = FormTestCase.client_author
        group_id = FormTestCase.group.id
        form_data = {'text': 'overwrited_post', 'group': group_id, }
        response = client.post(page, data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, page_redirect)

        edited_post = Post.objects.get(id=FormTestCase.post.id)
        edited_post_atributes = {'author': FormTestCase.user_author,
                                 'group_id': form_data['group'],
                                 'text': form_data['text']}
        for field, val in edited_post_atributes.items():
            with self.subTest(field=field):
                self.assertEqual(edited_post.__getattribute__(field), val)

    def test_created_comment_added_on_correct_pages(self):
        """Checks that the created comment appears on the correct pages"""
        client = FormTestCase.client_author
        post = FormTestCase.post
        page = reverse('posts:add_comment', kwargs={"post_id": post.pk})
        page_redirect = FormTestCase.page_reversed_name['post_detail']
        form_data = {'text': 'test_comment'}
        response = client.post(page, form_data, follow=True,)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, page_redirect)
        comment_text = response.context['comments'][0].text
        self.assertEqual(comment_text, form_data['text'])

    def test_guest_user_cant_create_comment(self):
        """Checks that the guest user  cant created comment"""
        client = FormTestCase.client_guest
        pages_redirect = (FormTestCase.page_reversed_name['login'],
                          FormTestCase.page_reversed_name['add_comment'])
        expected_comments_count = Comment.objects.count()
        form_data = {'text': 'impossible_comment'}
        response = client.post(
            FormTestCase.page_reversed_name['add_comment'],
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, '?next='.join(pages_redirect))
        self.assertEqual(Comment.objects.count(), expected_comments_count)
