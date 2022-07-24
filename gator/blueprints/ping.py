"""Blueprint that exposes endpoints for pinging the Gator API and
other critical services.
"""
from flask import Blueprint

bp = Blueprint('ping', __name__, url_prefix='/ping')


@bp.get('/')
def index():
    """"An endpoint for checking if the Gator service is up and running.
    
    It does not report the health of the service, just whether it is
    reachable (i.e. running).  The return value of this endpoint can be
    anything as long as the response has a status code of 200.
    """
    return 'pong'
    
