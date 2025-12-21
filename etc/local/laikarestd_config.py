import multiprocessing
import os

# Local development Gunicorn configuration file.
# Uses sync worker instead of gevent to avoid dependency issues

bind = os.getenv('LAIKRESTD_BIND', '0.0.0.0:8123')
backlog = 2048

workers = 2
# Use sync worker for local development (gevent has dependency issues)
worker_class = 'sync'
worker_connections = 1000
timeout = 90
keepalive = 2

spew = False

daemon = False
pidfile = None
user = None
group = None
umask = 0
tmp_upload_dir = None

errorlog = '-'
accesslog = '-'
logfile = '-'
loglevel = 'debug'
access_log_format = '%(t)s %(h)s %(l)s %({REMOTE_USER}e)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({EPHID}e)s" %({SUBMITID}e)s "%({SOURCE}e)s" "%({FILENAME}e)s" "%({LOOKUP_KEYS}e)s"'

proc_name = None

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
