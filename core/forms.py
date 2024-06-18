from typing import ClassVar

from django import forms

from .models import Post


class CommentForm(forms.ModelForm):
    class Meta:
        model: ClassVar = Post
        fields: ClassVar = ["content"]
        widgets: ClassVar = {
            "content": forms.Textarea(attrs={"rows": 3, "class": "form-control bg-dark text-light"}),
        }
        labels: ClassVar = {
            "content": "Add a comment:",
        }
