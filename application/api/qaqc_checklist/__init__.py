from flask import Blueprint

qaqc_checklist_bp = Blueprint('qaqc_checklist_bp', __name__, url_prefix='/qaqc-checklist')

from . import routes
