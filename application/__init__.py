import os
from logging.config import dictConfig

from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from mongoengine import connect

load_dotenv()

app = Flask(__name__)
CORS(app)
Mail(app)

if os.environ.get('FLASK_ENV') == 'development':
    print('Development mode, connecting to local MongoDB instance')
    connect('review_db', port=27017)
else:
    from flask_sslify import SSLify
    SSLify(app)
    connect(
        'review_db',
        host='review_mongo',
        port=27017,
        username=os.environ.get('MONGO_USERNAME'),
        password=os.environ.get('MONGO_PASSWORD'),
        authentication_source='admin'
    )

from application import routes
from application.api.attracted import attracted_bp
from application.api.comment import comment_bp
from application.api.dropcam_fieldbook import dropcam_fieldbook_bp
from application.api.image_reference import image_reference_bp
from application.api.qaqc_checklist import qaqc_checklist_bp
from application.api.reviewer import reviewer_bp
from application.api.stats import stats_bp
from application.logging_config import logging_config
from application.site import site_bp

dictConfig(logging_config)
app.config.from_object('application.config.Config')
app.register_blueprint(attracted_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(dropcam_fieldbook_bp)
app.register_blueprint(image_reference_bp)
app.register_blueprint(qaqc_checklist_bp)
app.register_blueprint(reviewer_bp)
app.register_blueprint(site_bp)
app.register_blueprint(stats_bp)
