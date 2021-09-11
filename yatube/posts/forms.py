from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'text',
            'group',
            'image'
        )
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, не обязательна для выбора'
        }
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'pub_date': 'Дата создания',
            'image': 'Картинка',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'text',
        )
