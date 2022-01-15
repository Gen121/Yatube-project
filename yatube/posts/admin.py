from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostInline(admin.TabularInline):
    model = Post
    extra = 1
    readonly_fields = ('author',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
        'image',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pk',
        'get_posts_count',
        'slug',
        'description',
    )
    search_fields = ('description',)
    ListFilter = ('-pk', 'posts',)
    empty_value_display = '-пусто-'
    save_on_top = True
    inlines = [PostInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'created',
        'post',
        'author',
    )
    search_fields = ('text',)
    list_filter = ('created',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author'
    )
    list_filter = ('user', 'author')
