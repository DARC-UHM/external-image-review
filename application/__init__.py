import os

from logging.config import dictConfig
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from flask_sslify import SSLify
from mongoengine import connect

mongo_username = os.environ["MONGO_USERNAME"]
mongo_password = os.environ["MONGO_PASSWORD"]
from application.logging_config import logging_config

dictConfig(logging_config)
load_dotenv()

app = Flask(__name__)
connect(
    'review_db', 
    host='review_mongo',
    port=27017,
    username=mongo_username,
    password=mongo_password,
    authentication_source='admin'
)
app.config.from_object('application.config.Config')

cors = CORS(app)
sslify = SSLify(app)
mail = Mail(app)

from application import routes
