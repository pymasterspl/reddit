from django import template
from django.contrib.auth import get_user_model

from core.models import Post

register = template.Library()

User = get_user_model()


@register.filter
def is_saved(post: Post, user: User) -> bool:
    if isinstance(post, Post):
        return post.is_saved(user)
    return False
