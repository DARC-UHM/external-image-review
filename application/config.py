import os


class Config:
    JSONIFY_PRETTYPRINT_REGULAR = True
    CORS_HEADERS = 'Content-Type'
    API_KEY = os.environ.get('API_KEY')
    TATOR_URL = 'https://cloud.tator.io'
    HURLSTOR_URL = 'http://hurlstor.soest.hawaii.edu'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
