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

def test_get_achievements(client):
    """Тест получения списка достижений"""
    response = client.get('/api/achievements')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) > 0
    assert 'id' in data[0]
    assert 'name' in data[0]
    assert 'reward' in data[0]
