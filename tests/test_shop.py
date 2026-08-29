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

def test_get_shop_returns_upgrades(client):
    """Test that shop returns upgrades"""
    response = client.get('/api/shop')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) > 0
    assert 'shawarma' in data
    assert 'coffee' in data

def test_buy_upgrade_success(client):
    """Test successful purchase"""
    unique_id = f"test_buyer_{int(time.time())}"
    client.get(f'/api/player/{unique_id}')
    
    from app.database import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE players SET balance = 1000 WHERE chat_id = ?", (unique_id,))
    conn.commit()
    conn.close()
    
    response = client.post(f'/api/buy/{unique_id}/shawarma')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] == True
    assert data['balance'] < 1000

def test_buy_upgrade_insufficient_funds(client):
    """Test purchase without money"""
    unique_id = f"test_broke_{int(time.time())}"
    client.get(f'/api/player/{unique_id}')
    
    response = client.post(f'/api/buy/{unique_id}/spaceport')
    assert response.status_code == 400
    
    data = response.get_json()
    assert 'error' in data
