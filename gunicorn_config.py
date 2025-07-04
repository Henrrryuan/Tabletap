import multiprocessing

bind = "127.0.0.1:8001"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
keepalive = 5
errorlog = "logs/gunicorn-error.log"
accesslog = "logs/gunicorn-access.log"
loglevel = "debug"
capture_output = True
pythonpath = "/home/s4865883/www/djangoapps/tabletap"

# Logging
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/gunicorn-debug.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'gunicorn.error': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': True,
        },
        'gunicorn.access': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': True,
        },
    }
} 