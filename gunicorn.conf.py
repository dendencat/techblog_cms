import multiprocessing
import os

# Get the directory containing this file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Basic configurations
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"  # Changed from gevent to sync for stability
timeout = 120
keepalive = 5

# Path configurations
pythonpath = '/app'
chdir = '/app'
wsgi_app = 'techblog_cms.wsgi:application'  # Updated WSGI path

# Logging
errorlog = os.path.join(current_dir, 'logs/error.log')
accesslog = os.path.join(current_dir, 'logs/access.log')
loglevel = 'debug'

# Development settings
reload = os.environ.get('DEBUG', 'False').lower() == 'true'
capture_output = True
enable_stdio_inheritance = True
