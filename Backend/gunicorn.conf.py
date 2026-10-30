import os

# Gunicorn configuration for Render deployment
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = int(os.environ.get("PYTHON_GET_THREADS", 2))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
