from app import create_app
from app.database import init_db
import pytest
import os
import time

@pytest.fixture
def app():
    os.environ['DATABASE_URL'] = ''
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        init_db()
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_player_creates_new(client):
    """Test that new player is created"""
    unique_id = f"test_user_{int(time.time())}_1"
    response = client.get(f'/api/player/{unique_id}')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['chat_id'] == unique_id
    assert data['balance'] == 0
    assert data['level'] == 1

def test_click_increases_balance(client):
    """Test that click increases balance"""
    unique_id = f"test_user_{int(time.time())}_2"
    client.get(f'/api/player/{unique_id}')
    
    response = client.post(f'/api/click/{unique_id}')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['balance'] >= 10
    assert data['clicks'] == 1
