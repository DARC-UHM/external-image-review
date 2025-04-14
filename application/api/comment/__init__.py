from flask import Blueprint

comment_bp = Blueprint('comment_bp', __name__, url_prefix='/comment')

from . import routes
