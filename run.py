from app import create_app
from app.database import init_db

# Инициализируем БД
init_db()

# Создаём приложение
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
