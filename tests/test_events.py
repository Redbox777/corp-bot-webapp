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

def test_start_event(client):
    """Тест запуска события"""
    client.get('/api/player/test_event_user')
    
    response = client.post('/api/events/start/test_event_user')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] == True
    assert 'event' in data
    assert 'end_time' in data

def test_event_status(client):
    """Тест статуса события"""
    client.get('/api/player/test_event_status')
    
    # Сначала нет активного события
    response = client.get('/api/events/status/test_event_status')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['active'] == False
