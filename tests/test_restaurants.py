import pytest
from rest_framework.test import APIClient
from users.models import User

@pytest.fixture
def customer_client(db):
    user = User.objects.create_user(
        username='customer1',
        email='customer@test.com',
        password='test1234',
        role='customer'
    )
    client = APIClient()
    response = client.post('/api/users/login/', {
        'email': 'customer@test.com',
        'password': 'test1234'
    })
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['tokens']['access'])
    return client

def test_customer_cannot_create_restaurant(customer_client):
    response = customer_client.post('/api/restaurants/create/', {
        'name': 'Test Restaurant',
        'address': '123 Test St',
        'phone': '9999999999'
    })
    assert response.status_code == 403

def test_place_order(customer_client):
    response = customer_client.get('/api/orders/my-orders/')
    assert response.status_code == 200

def test_404_on_wrong_restaurant_id(customer_client):
    response = customer_client.get('/api/restaurants/99999/')
    assert response.status_code == 404