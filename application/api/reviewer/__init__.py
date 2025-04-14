from flask import Blueprint

reviewer_bp = Blueprint('reviewer_bp', __name__, url_prefix='/reviewer')

from . import routes
