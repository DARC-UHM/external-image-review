from flask import Blueprint

dropcam_fieldbook_bp = Blueprint('dropcam_fieldbook_bp', __name__)

from . import routes
