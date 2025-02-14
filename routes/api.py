from flask import Blueprint, request, jsonify

# create the blueprint for this one:
api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

@api_bp.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        return jsonify({"message": "Data received"})
    else:
        return jsonify({"message": "this is the 'GET' endpoint, now lets see how this changes when I edit this thing"})










