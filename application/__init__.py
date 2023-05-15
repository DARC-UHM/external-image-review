import os
from flask import Flask
from mongoengine import connect

mongo_username = os.environ["MONGO_USERNAME"]
mongo_password = os.environ["MONGO_PASSWORD"]

app = Flask(__name__)
connect('review_mongo', username=mongo_username, password=mongo_password)

from application import routes
