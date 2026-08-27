# Compatibility layer for Render
# Render expects server.py but we use main.py
from main import app

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
