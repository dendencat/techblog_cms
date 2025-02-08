import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
errorlog = '-'
accesslog = '-'
capture_output = True
enable_stdio_inheritance = True
reload = True
wsgi_app = 'techblog.wsgi:application'
chdir = '/app'
