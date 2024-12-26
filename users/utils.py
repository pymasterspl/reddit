from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from reddit import settings

from .models import User
from .tokens import account_activation_token


def user_creation(user: User, request: HttpRequest) -> User:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    protocol = "https" if request.is_secure() else "http"
    current_site = get_current_site(request)
    activation_link = reverse("activate-account", kwargs={"uidb64": uid, "token": token})
    full_activation_link = f"{protocol}://{current_site.domain}{activation_link}"
    send_mail(
        "Confirm your registration",
        f"Please click on the following link to confirm your registration " f"{activation_link}",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
        html_message=render_to_string(
            "users/account_activation_email.html",
            {
                "user": user,
                "activation_link": full_activation_link,
            },
        ),
    )
    return user
