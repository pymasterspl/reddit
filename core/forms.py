import typing
from typing import ClassVar

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import REPORT_CHOICES, Community, Post, PostReport


class CommentForm(forms.Form):
    content = forms.CharField(
        label="Add a comment",
        required=True,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control bg-dark text-light",
            },
        ),
    )
    parent_id = forms.IntegerField(required=True, widget=forms.HiddenInput)


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
        super().__init__(*args, **kwargs)
        self.fields["community"].queryset = Community.objects.filter(
            is_active=True)
        self.fields["title"].required = True
        self.fields["content"].required = True


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields: typing.ClassVar = ["name"]

    def __init__(self: "CommunityForm", *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Create Community"))


class PostReportForm(forms.ModelForm):
    report_type: ClassVar[forms.ChoiceField] = forms.ChoiceField(
        choices=REPORT_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = PostReport
        fields: ClassVar[list[str]] = ["post", "report_type", "report_details", "report_person"]
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "post": forms.HiddenInput(),
            "report_person": forms.HiddenInput(),
            "report_details": forms.Textarea(attrs={"class": "form-control"}),
        }


class AdminActionForm(forms.Form):
    ACTION_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("BAN", "Ban User"),
        ("DELETE", "Delete Post"),
        ("WARN", "Warn User"),
        ("OKEY", "Okey"),
    ]
    action: ClassVar[forms.ChoiceField] = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}))
    comment: ClassVar[forms.Textarea] = forms.CharField(widget=forms.Textarea,
                                                        required=False)
