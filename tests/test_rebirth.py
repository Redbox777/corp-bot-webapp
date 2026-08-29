from app import create_app
from app.database import init_db
import pytest
import os

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

def test_rebirth_requires_level(client):
    """Тест что перерождение требует уровень"""
    client.get('/api/player/test_rebirth_low')
    
    response = client.post('/api/rebirth/test_rebirth_low')
    assert response.status_code == 400
    
    data = response.get_json()
    assert 'error' in data

def test_rebirth_success(client):
    """Тест успешного перерождения"""
    # Создаём игрока с высоким уровнем
    client.get('/api/player/test_rebirth_high')
    
    from app.database import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE players SET level = 10, total_earned = 10000 WHERE chat_id = 'test_rebirth_high'")
    conn.commit()
    conn.close()
    
    response = client.post('/api/rebirth/test_rebirth_high')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] == True
    assert data['gems_added'] > 0
