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

def test_leaderboard_empty(client):
    """Тест пустой таблицы лидеров"""
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    
    data = response.get_json()
    assert isinstance(data, list)
