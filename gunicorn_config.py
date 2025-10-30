#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gunicorn configuration for production deployment
"""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = "-"
loglevel = "info"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "viddy_downloader"

# Server hooks
def on_starting(server):
    """
    Called just before the master process is initialized.
    """
    pass

def on_reload(server):
    """
    Called to recycle workers during a reload via SIGHUP.
    """
    pass

def when_ready(server):
    """
    Called just after the server is started.
    """
    print("Gunicorn server is ready. Application running in production mode!")