from flask import Flask
from mongoengine import connect

app = Flask(__name__)
connect('comments')

from application import routes
