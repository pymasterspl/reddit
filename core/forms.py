import typing
from typing import ClassVar

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.core.exceptions import ValidationError

from .models import Community, Post, User, PostAward


class CommentForm(forms.Form):
    MAX_COMMENT_LENGTH = 500
    content = forms.CharField(
        label="Add a comment",
        required=True,
        max_length=MAX_COMMENT_LENGTH,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control bg-dark text-light",
                "maxlength": MAX_COMMENT_LENGTH,
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

class IconRadioSelect(forms.RadioSelect):
    template_name = 'core/icon_radio_select.html'

class PostAwardForm(forms.ModelForm):
    class Meta:
        model = PostAward
        fields = ['choice', 'anonymous', 'comment']
        widgets = {
            'choice': IconRadioSelect(attrs={'class': 'form-check-input', 'required': True}),
            'anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional comment'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['choice'].choices = [choice for choice in self.fields['choice'].choices if choice[0] != '']

    def clean(self):
        cleaned_data = super().clean()
        anonymous = cleaned_data.get('anonymous')
        comment = cleaned_data.get('comment')

        if anonymous and comment:
            self.add_error('comment', 'You cannot add a comment to an anonymous award.')

        return cleaned_data


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
        self.fields["is_18_plus"].label = "Mature (18+) - only users over 18 can view and contribute"


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
