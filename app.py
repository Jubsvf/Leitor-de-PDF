"""
Ponto de entrada padrão para servidores WSGI (como Gunicorn no Render).
Importa a aplicação Flask configurada em server.py.
"""
from server import app

if __name__ == "__main__":
    app.run()
