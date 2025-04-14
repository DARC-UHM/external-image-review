from flask import Blueprint

attracted_bp = Blueprint('attracted_bp', __name__, url_prefix='/attracted')

from . import routes
