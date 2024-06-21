from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.utils.text import slugify

from core.models import Community


class CommentForm(forms.Form):
    content = forms.CharField(label="Add a comment", required=True, widget=forms.Textarea(
        attrs={
            "rows": 3,
            "class": "form-control bg-dark text-light",
        },
    ))
    parent_id = forms.IntegerField(required=True, widget=forms.HiddenInput)


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create Community'))

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance
