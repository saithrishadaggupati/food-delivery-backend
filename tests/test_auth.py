import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username='testcustomer',
        email='customer@test.com',
        password='test1234',
        role='customer'
    )


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username='testowner',
        email='owner@test.com',
        password='test1234',
        role='restaurant_owner'
    )


def test_register_success(client, db):
    response = client.post('/api/users/register/', {
        'username': 'newuser',
        'email': 'newuser@test.com',
        'password': 'test1234',
        'role': 'customer'
    }, format='json')
    assert response.status_code == 201
    assert response.data['message'] == 'Account created successfully!'


def test_register_duplicate_fails(client, customer, db):
    response = client.post('/api/users/register/', {
        'username': 'testcustomer',
        'email': 'customer@test.com',
        'password': 'test1234',
        'role': 'customer'
    }, format='json')
    assert response.status_code == 400


def test_login_success(client, customer, db):
    response = client.post('/api/users/login/', {
        'email': 'customer@test.com',
        'password': 'test1234'
    }, format='json')
    assert response.status_code == 200
    assert 'tokens' in response.data


def test_login_wrong_password(client, customer, db):
    response = client.post('/api/users/login/', {
        'email': 'customer@test.com',
        'password': 'wrongpassword'
    }, format='json')
    assert response.status_code == 401


def test_profile_requires_auth(client, db):
    response = client.get('/api/users/profile/')
    assert response.status_code == 401