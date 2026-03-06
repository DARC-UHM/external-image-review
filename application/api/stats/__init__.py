from flask import Blueprint

stats_bp = Blueprint('stats_bp', __name__, url_prefix='/stats')

from . import routes
