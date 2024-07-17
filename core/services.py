from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpRequest

from core.models import PostReport
from users.models import User


def handle_admin_action(action: str, report: PostReport, user: User, request: HttpRequest) -> None:
    if action == "BAN":
        report.verified = True
        report.save()
        user.create_post = False
        user.save()
        report.post.delete()
        send_mail(
            "Account Banned",
            "Your account has been banned for violating community rules, now you cannot access posts.",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, "User has been banned successfully.")
    elif action == "DELETE":
        report.verified = True
        report.save()
        report.post.delete()
        send_mail(
            "Post Deleted",
            "Your post has been deleted due to violations of community guidelines.",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, "Post has been deleted successfully.")
    elif action == "WARN":
        user.warnings += 1
        report.verified = True
        report.save()
        if user.warnings >= settings.LIMIT_WARNINGS:
            report.post.delete()
            send_mail(
                "Post Deleted",
                "Your post has been deleted due to violations of community guidelines.",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, "Post has been deleted successfully.")
        else:
            send_mail(
                "Warning Issued",
                "You have received a warning due to violations of community guidelines.",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, "User has been warned successfully.")
    elif action == "ACCEPT":
        report.verified = True
        report.save()
    else:
        pass
