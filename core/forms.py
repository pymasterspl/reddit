from typing import ClassVar

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import Community, Post, PostReport


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
        fields: ClassVar = ["name"]

    def __init__(self: "CommunityForm", *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Create Community"))


class PostReportForm(forms.ModelForm):
    BREAKS_RULES = "BREAKS_RULES"
    EU_ILLEGAL_CONTENT = "EU_ILLEGAL_CONTENT"
    HARASSMENT = "HARASSMENT"
    THREATENING_VIOLENCE = "THREATENING_VIOLENCE"
    HATE = "HATE"
    MINOR_ABUSE_OR_SEXUALIZATION = "MINOR_ABUSE_OR_SEXUALIZATION"
    SHARING_PERSONAL_INFORMATION = "SHARING_PERSONAL_INFORMATION"
    NON_CONSENSUAL_INTIMATE_MEDIA = "NON_CONSENSUAL_INTIMATE_MEDIA"
    PROHIBITED_TRANSACTION = "PROHIBITED_TRANSACTION"
    IMPERSONATION = "IMPERSONATION"
    COPYRIGHT_VIOLATION = "COPYRIGHT_VIOLATION"
    TRADEMARK_VIOLATION = "TRADEMARK_VIOLATION"
    SELF_HARM_OR_SUICIDE = "SELF_HARM_OR_SUICIDE"
    SPAM = "SPAM"
    REPORT_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (BREAKS_RULES, "Breaks r/fatFIRE rules"),
        (EU_ILLEGAL_CONTENT, "EU illegal content"),
        (HARASSMENT, "Harassment"),
        (THREATENING_VIOLENCE, "Threatening violence"),
        (HATE, "Hate"),
        (MINOR_ABUSE_OR_SEXUALIZATION, "Minor abuse or sexualization"),
        (SHARING_PERSONAL_INFORMATION, "Sharing personal information"),
        (NON_CONSENSUAL_INTIMATE_MEDIA, "Non-consensual intimate media"),
        (PROHIBITED_TRANSACTION, "Prohibited transaction"),
        (IMPERSONATION, "Impersonation"),
        (COPYRIGHT_VIOLATION, "Copyright violation"),
        (TRADEMARK_VIOLATION, "Trademark violation"),
        (SELF_HARM_OR_SUICIDE, "Self-harm or suicide"),
        (SPAM, "Spam"),
    ]
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
    BAN = "BAN"
    DELETE = "DELETE"
    WARN = "WARN"
    DISMISS_REPORT = "DISMISS_REPORT"
    ACTION_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (BAN, "Ban User"),
        (DELETE, "Delete Post"),
        (WARN, "Warn User"),
        (DISMISS_REPORT, "Dismiss Report"),
    ]
    action: forms.ChoiceField = forms.ChoiceField(
        choices=ACTION_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
    comment: forms.Textarea = forms.CharField(widget=forms.Textarea, required=False)
