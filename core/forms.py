from typing import ClassVar

from django import forms


class CommentForm(forms.Form):
    content = forms.CharField(required=True, widget=forms.Textarea(
        attrs={
            "rows": 3,
            "class": "form-control bg-dark text-light",
        },
    ),
                              )
    parent_id = forms.IntegerField(required=True, widget=forms.HiddenInput)

    class Meta:
        fields: ClassVar[list[str]] = ["content", "parent_id"]
        labels: ClassVar[dict[str, str]] = {
            "content": "Add a comment:",
        }
