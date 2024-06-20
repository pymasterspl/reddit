from django import forms


class CommentForm(forms.Form):
    content = forms.CharField(required=True, widget=forms.Textarea(attrs={"rows": 3, "class": "form-control bg-dark text-light"}))
    parent_id = forms.IntegerField(required=True, widget=forms.HiddenInput)

    class Meta:
        fields = ["content", "parent_id"]
        labels = {
            "content": "Add a comment:",
        }
