import os
from logging.config import dictConfig

from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from flask_sslify import SSLify
from mongoengine import connect

from application.api.attracted import attracted_bp
from application.api.comment import comment_bp
from application.api.dropcam_fieldbook import dropcam_fieldbook_bp
from application.api.qaqc_checklist import qaqc_checklist_bp
from application.api.reviewer import reviewer_bp
from application.api.stats import stats_bp
from application.logging_config import logging_config
from application.site import site_bp

dictConfig(logging_config)
load_dotenv()

app = Flask(__name__)
connect(
    'review_db',
    host='review_mongo',
    port=27017,
    username=os.environ["MONGO_USERNAME"],
    password=os.environ["MONGO_PASSWORD"],
    authentication_source='admin'
)
app.config.from_object('application.config.Config')
app.register_blueprint(attracted_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(dropcam_fieldbook_bp)
app.register_blueprint(qaqc_checklist_bp)
app.register_blueprint(reviewer_bp)
app.register_blueprint(site_bp)
app.register_blueprint(stats_bp)

cors = CORS(app)
sslify = SSLify(app)
mail = Mail(app)

from application import routes
