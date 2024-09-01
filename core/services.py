from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpRequest

from core.models import PostReport
from users.models import User

from .models import BAN, DELETE, DISMISS_REPORT, WARN


def handle_admin_action(action: str, report: PostReport, user: User, request: HttpRequest) -> None:
    if action == BAN:
        ban_user(request, report, user)
    elif action == DELETE:
        delete_post(request, report, user)
    elif action == WARN:
        warn_user(request, report, user)
    elif action == DISMISS_REPORT:
        dismiss_report(report)


def ban_user(request: HttpRequest, report: PostReport, user: User) -> None:
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


def delete_post(request: HttpRequest, report: PostReport, user: User) -> None:
    report.verified = True
    report.save()
    report.post.is_active = False
    report.post.save()
    send_mail(
        "Post Deleted",
        "Your post has been deleted due to violations of community guidelines.",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
    messages.success(request, "Post has been deleted successfully.")


def warn_user(request: HttpRequest, report: PostReport, user: User) -> None:
    user.warnings += 1
    report.verified = True
    report.save()
    if user.warnings >= settings.LIMIT_WARNINGS:
        report.post.is_active = False
        report.post.save()
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


def dismiss_report(report: PostReport) -> None:
    report.verified = True
    report.save()
