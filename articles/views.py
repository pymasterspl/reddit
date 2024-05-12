from django.http import HttpRequest
from django.shortcuts import render


def home_view(request: HttpRequest) -> HttpRequest:
    return render(request, "base.html")
