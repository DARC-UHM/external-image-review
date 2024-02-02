logging_config = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S %Z',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'external_review.log',
            'formatter': 'default',
        },
        'size-rotate': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'external_review.log',
            'maxBytes': 10000,
            'backupCount': 1,
            'formatter': 'default',
        },
    },
    'root': {'level': 'DEBUG', 'handlers': ['console', 'file']},
}
