"""Blueprint that exposes endpoints for pinging the Gator API and
other critical services.
"""
from flask import Blueprint

bp = Blueprint('ping', __name__, url_prefix='/ping')


@bp.get('/')
def index():
    return 'All good!'
