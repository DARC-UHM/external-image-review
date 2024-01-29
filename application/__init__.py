import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_sslify import SSLify
from mongoengine import connect

mongo_username = os.environ["MONGO_USERNAME"]
mongo_password = os.environ["MONGO_PASSWORD"]

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
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['API_KEY'] = os.environ.get('API_KEY')
app.config['TATOR_IMAGE_FOLDER'] = 'tator-images'

cors = CORS(app)
sslify = SSLify(app)

from application import routes
