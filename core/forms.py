from django import forms

from .models import Community, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["community", "title", "content"]
        widgets = {
            "community": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control"})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields["community"].queryset = Community.objects.filter(is_active=True)
