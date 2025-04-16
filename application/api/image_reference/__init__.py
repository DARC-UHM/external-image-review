from flask import Blueprint

image_reference_bp = Blueprint('image_reference_bp', __name__, url_prefix='/image-reference')

from . import routes
