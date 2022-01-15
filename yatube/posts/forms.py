from django import forms

from .models import Comment, Group, Post


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea,
                           help_text='Ваше слово, товарищ маузер',)
    group = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   required=False,
                                   empty_label='<Без_темы>',
                                   help_text='Семантическое поле')

    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {'text': 'Текст поста',
                  'group': 'Тематическая группа',
                  'image': 'Изображение', }

    def clean_text(self):
        text = self.cleaned_data['text']
        if not text:
            raise forms.ValidationError('Поле обязательно к заполнению!')
        return text


class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea,
                           help_text='Ваше слово, товарищ маузер',)

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария', }

    def clean_text(self):
        text = self.cleaned_data['text']
        if not text:
            raise forms.ValidationError('Поле обязательно к заполнению!')
        return text
