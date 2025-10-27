import os
from slack_sdk import WebClient


class Config:
    JSONIFY_PRETTYPRINT_REGULAR = True
    CORS_HEADERS = 'Content-Type'
    API_KEY = os.environ.get('API_KEY')
    TATOR_URL = 'https://cloud.tator.io'
    HURLSTOR_URL = 'http://hurlstor.soest.hawaii.edu'
    IMAGE_REF_DIR_PATH = 'application/image-reference'
    SLACK_CHANNEL_ID = os.environ.get('SLACK_CHANNEL_ID')
    SLACK_CLIENT = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
