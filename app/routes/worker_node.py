from flask import Blueprint, request, jsonify
from typing import cast
from app.extended_flask import ExtendedFlask

worker_node_bp = Blueprint('worker_node_bp', __name__, url_prefix='/node')

@worker_node_bp.route('/inbox', methods=['GET'])
def inbox():

    ##$$$$ MIGHT GET RID OF THIS LATER
    # app = cast(ExtendedFlask, current_app)
    # app.jobs_and_tasks_db.do_something(...)

    #This will return a JSON file for the worker that contains everything currently in its inbox.
    #Includes: Network speed tests, battery life, tasks to complete
    return jsonify({"Nothing yet": "test for inbox"})

@worker_node_bp.route('/outbox', methods=['POST'])
def outbox():
    #the Worker node will respond to the requests by publishing its answers here.
    # Includes: Network speed tests, battery life, results of tasks.
    return jsonify({"Nothing yet": "test for outbox"})