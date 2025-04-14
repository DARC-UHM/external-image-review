from flask import Blueprint

site_bp = Blueprint('site', __name__)

from . import routes
