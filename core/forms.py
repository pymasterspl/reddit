from typing import ClassVar

from django import forms

from .models import Community, Post


class PostForm(forms.ModelForm):
    user: forms.models.BaseModelForm | None

    class Meta:
        model = Post
        fields: ClassVar[list[str]] = ["community", "title", "content"]
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "community": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control"}),
        }

    def __init__(self: "Post", *args: tuple, **kwargs: dict) -> None:
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["community"].queryset = Community.objects.filter(is_active=True)
        self.fields["title"].required = True
        self.fields["content"].required = True
