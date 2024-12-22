import pytest
from django.contrib.auth import get_user_model

from users.forms import ConfirmDeleteAccountForm

User = get_user_model()


@pytest.mark.django_db()
def test_confirm_password_form_valid(user: User) -> None:
    form = ConfirmDeleteAccountForm(user, data={"password": user.plain_password})
    assert form.is_valid()


@pytest.mark.django_db()
def test_confirm_password_form_invalid_password(user: User) -> None:
    wrong_password = user.plain_password + "wrong"
    form = ConfirmDeleteAccountForm(user, data={"password": wrong_password})
    assert not form.is_valid()
    assert form.errors["password"] == ["Incorrect password."]


@pytest.mark.django_db()
def test_confirm_password_form_empty_password(user: User) -> None:
    form = ConfirmDeleteAccountForm(user, data={"password": ""})
    assert not form.is_valid()
    assert form.errors["password"] == ["This field is required."]
