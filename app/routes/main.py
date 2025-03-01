from flask import Blueprint, request, jsonify
from typing import cast
from app.extended_flask import ExtendedFlask

# create the blueprint for this one:
main_bp = Blueprint('main_bp', __name__, url_prefix='/')

@main_bp.route('/', methods=['GET'])
def main():
    return jsonify({"Nothing yet": "test2"})






