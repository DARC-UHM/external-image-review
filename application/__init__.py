import os
from flask import Flask
from flask_sslify import SSLify
from mongoengine import connect

mongo_username = os.environ["MONGO_USERNAME"]
mongo_password = os.environ["MONGO_PASSWORD"]

app = Flask(__name__)
connect(
    'review_db', 
    host='review_mongo',
    port=27017,
    username=mongo_username,
    password=mongo_password,
    authentication_source='admin'
)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

sslify = SSLify(app)

from application import routes
