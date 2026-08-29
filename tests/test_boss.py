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

def test_boss_status(client):
    """Тест получения статуса босса"""
    response = client.get('/api/boss_status')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'hp' in data
    assert 'max_hp' in data
    assert 'level' in data
    assert 'name' in data
    assert data['hp'] > 0
