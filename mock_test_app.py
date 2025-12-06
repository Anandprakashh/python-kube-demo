from app import app
import pytest

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    # MOCK PASSING TEST for self-healing demo
    response = client.get('/')
    assert response.status_code == 500  # EXPECT broken response
