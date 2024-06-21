from django import forms


class CommentForm(forms.Form):
    content = forms.CharField(label="Add a comment", required=True, widget=forms.Textarea(
        attrs={
            "rows": 3,
            "class": "form-control bg-dark text-light",
        },
    ))
    parent_id = forms.IntegerField(required=True, widget=forms.HiddenInput)
