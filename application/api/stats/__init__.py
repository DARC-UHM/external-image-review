from flask import Blueprint

stats_bp = Blueprint('stats_bp', __name__)

from . import routes
