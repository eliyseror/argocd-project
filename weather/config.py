
import multiprocessing

bind = 'unix:/tmp/gunicorn.sock'  # Bind to a Unix socket
workers = multiprocessing.cpu_count() * 2 + 1  # Number of worker processes
worker_class = 'gunicorn.workers.ggevent.GeventWorker'  # Type of worker
timeout = 30  # Time to wait for a request before timing out
loglevel = 'info'  # Logging level
accesslog = '-'  # Log to stdout
errorlog = '-'  # Log to stderr
