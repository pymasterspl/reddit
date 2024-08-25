import typing
from typing import ClassVar

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.core.exceptions import ValidationError

from .models import ACTION_CHOICES, REPORT_CHOICES, Community, Post, PostReport, User


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
        self.fields["community"].queryset = Community.objects.filter(is_active=True)
        self.fields["title"].required = True
        self.fields["content"].required = True


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields: typing.ClassVar = ["name", "privacy", "is_18_plus"]

    def __init__(self: "CommunityForm", *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Create Community"))
        self.fields["is_18_plus"].widget = forms.CheckboxInput()
        self.fields[
            "is_18_plus"].label = "Mature (18+) - only users over 18 can view and contribute"

class PostReportForm(forms.ModelForm):
    report_type: forms.ChoiceField = forms.ChoiceField(
        choices=REPORT_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = PostReport
        fields: ClassVar[list[str]] = ["report_type", "report_details"]
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "report_details": forms.Textarea(attrs={"class": "form-control"}),
        }


class AdminActionForm(forms.Form):
    action: forms.ChoiceField = forms.ChoiceField(
        choices=ACTION_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
    comment: forms.Textarea = forms.CharField(widget=forms.Textarea, required=False)



class AddModeratorForm(forms.Form):
    nickname = forms.CharField(max_length=150, help_text="Enter the nickname of the user to add as a moderator.")

    def clean_nickname(self: "AddModeratorForm") -> User:
        nickname = self.cleaned_data.get("nickname")
        user_not_found_message = "User with this nickname does not exist."
        try:
            user = User.objects.get(nickname=nickname)
        except User.DoesNotExist as err:
            raise ValidationError(user_not_found_message) from err
        return user


class RemoveModeratorForm(forms.Form):
    nickname = forms.CharField(max_length=150, help_text="Enter the nickname of the user to remove from moderators.")

    def clean_nickname(self: "RemoveModeratorForm") -> User:
        nickname = self.cleaned_data.get("nickname")
        user_not_found_message = "User with this nickname does not exist."
        try:
            user = User.objects.get(nickname=nickname)
        except User.DoesNotExist as err:
            raise ValidationError(user_not_found_message) from err
        return user
