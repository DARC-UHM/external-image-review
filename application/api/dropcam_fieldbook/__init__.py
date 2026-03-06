from flask import Blueprint

dropcam_fieldbook_bp = Blueprint('dropcam_fieldbook_bp', __name__, url_prefix='/dropcam-fieldbook')

from . import routes
