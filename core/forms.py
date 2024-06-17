from django import forms

from .models import Community, Post


class PostForm(forms.ModelForm):
  class Meta:
    model = Post
    fields = ["community", "title", "content"]
    widgets = {
      "community": forms.Select(attrs={"class": "form-select"}),
    }

  def __init__(self, *args, **kwargs):
    super(PostForm, self).__init__(*args, **kwargs)
    self.fields["community"].queryset = Community.objects.filter(is_active=True)

