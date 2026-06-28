from flask import Blueprint

annotation_bp = Blueprint('annotation_bp', __name__, url_prefix='/annotation')

from . import routes
