
import pytest
from core.forms import ContactForm
from django.urls import reverse

def test_contactform_exists():
    ContactForm(data={})

def test_contactform_no_data():
    form = ContactForm(data={})
    assert not form.is_valid()
    assert len(form.errors) == 3

def test_contactform_valid_data():
    form = ContactForm(data={
        'name': 'Jacek',
        'email': 'jacek@example.com',
        'message': 'Cześć!'
    })
    assert form.is_valid()

def test_form_missing_name():
    form = ContactForm(data={
        'email': 'jacek@example.com',
        'message': 'Cześć!'
    })
    assert not form.is_valid()
    assert 'name' in form.errors

def test_form_missing_email():
    form = ContactForm(data={
        'name': 'Jacek',
        'message': 'Cześć!'
    })
    assert not form.is_valid()
    assert 'email' in form.errors

def test_form_missing_message():
    form = ContactForm(data={
        'name': 'Jacek',
        'email': 'jacek@example.com'
    })
    assert not form.is_valid()
    assert 'message' in form.errors

def test_form_invalid_email():
    form = ContactForm(data={
        'name': 'Jacek',
        'email': 'not-an-email',
        'message': 'Cześć!'
    })
    assert not form.is_valid()
    assert 'email' in form.errors

@pytest.mark.django_db
def test_form_success(client):
    response = client.post(reverse('contact'), {
        'name': 'Jacek',
        'email': 'jacek@example.com',
        'message': 'Cześć!'
    }, follow=True)
    assert response.status_code == 200
    assert len(response.context["form"].errors) == 0