from flask import Blueprint

# first want to create a blueprint:
index_bp = Blueprint('index_bp', __name__)

@index_bp.route('/')
def index():
    """
    A simple route that returns a text response.
    """
    return "index blueprint"
