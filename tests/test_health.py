from app import create_app
import pytest
import os

@pytest.fixture
def app():
    """Создаём тестовое приложение с SQLite"""
    os.environ['DATABASE_URL'] = ''  # Пустая строка = SQLite
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    """Тест health check"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'version' in data

def test_health_returns_json(client):
    """Тест что возвращается JSON"""
    response = client.get('/health')
    assert response.content_type == 'application/json'
