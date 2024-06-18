from django import forms

from .models import Post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, 'class': 'form-control bg-dark text-light'}),
        }
        labels = {
            "content": "Add a comment:",
        }
