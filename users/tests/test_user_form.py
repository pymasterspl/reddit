import pytest
from django.contrib.auth import get_user_model

from users.forms import ConfirmDeleteAccountForm, EmailChangeForm

User = get_user_model()


@pytest.mark.django_db()
def test_confirm_password_form_valid(user: User) -> None:
    form = ConfirmDeleteAccountForm(user, data={"password": user.plain_password})
    assert form.is_valid()


@pytest.mark.django_db()
def test_confirm_password_form_invalid_password(user: User) -> None:
    wrong_password = f"{user.plain_password}wrong"
    form = ConfirmDeleteAccountForm(user, data={"password": wrong_password})
    assert not form.is_valid()
    assert form.errors["password"] == ["Incorrect password."]


@pytest.mark.django_db()
def test_confirm_password_form_empty_password(user: User) -> None:
    form = ConfirmDeleteAccountForm(user, data={"password": ""})
    assert not form.is_valid()
    assert form.errors["password"] == ["This field is required."]


@pytest.mark.django_db()
def test_change_email_form_valid(user: User) -> None:
    new_email = "new_email@example.com"
    form = EmailChangeForm(data={"old_email": user.email, "new_email": new_email, "new_email_confirmation": new_email})
    assert form.is_valid()


@pytest.mark.django_db()
def test_change_email_not_same_new_emails_invalid(user: User) -> None:
    new_email = "new_email@example.com"
    form = EmailChangeForm(
        data={"old_email": user.email, "new_email": new_email, "new_email_confirmation": new_email + "test"}
    )
    assert not form.is_valid()
    assert form.errors["new_email"] == ["Provided emails are not the same"]


@pytest.mark.django_db()
def test_change_email_form_empty_email_invalid(user: User) -> None:
    form = EmailChangeForm(data={"old_email": ""})
    assert not form.is_valid()
    assert form.errors["old_email"] == ["This field is required."]


@pytest.mark.django_db()
def test_change_email_used_occupied_email_form_valid(user: User) -> None:
    form = EmailChangeForm(
        data={"old_email": user.email, "new_email": user.email, "new_email_confirmation": user.email}
    )
    assert not form.is_valid()
    assert form.errors["new_email"] == ["This email is already in use"]
