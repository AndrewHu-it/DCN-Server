import os
import secrets
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, abort, current_app
from typing import cast
from app.extended_flask import ExtendedFlask

"""
A Few NOTES: 
- Need to consider what happens when we turn off a node in the middle of processing a task.
"""



worker_node_bp = Blueprint('worker_node_bp', __name__, url_prefix='/node')

#COMPLETED
@worker_node_bp.route('/register', methods=['POST'])
def register_node():
    json_data = request.get_json()
    if not json_data or 'name' not in json_data:
        abort(400, description='Missing name')

    try:
        # Unpack information
        name = json_data['name']
        compute_specs = json_data.get('compute_specs', {})
        cpu = str(compute_specs.get('cpu', 'Not specified'))
        gpu = str(compute_specs.get('gpu', 'Not specified'))
        cores = (compute_specs.get('cores', 'Not specified'))
        ram = str(compute_specs.get('ram', 'Not specified'))
        node_id = str(uuid.uuid4())
        availability = True


        # Create new node record
        new_node = {
            "node_id": node_id,
            "name": name,
            "date_joined": {"$date": datetime.utcnow().isoformat() + "Z"},
            "available": availability,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_computations": 0,
            "value_of_computations": 0,
            "computer_specs": {
                "cpu": cpu,
                "gpu": gpu,
                "cores": cores,
                "ram": ram
            }
        }

        app = cast(ExtendedFlask, current_app)
        job_result = app.computing_nodes_db.add("all_nodes", new_node)

        #Keed in mind, Inbox and Outbox are from the perspective of the node.
        dump = "dump_"+ node_id
        node_inbox: str = "inbox_"+ node_id
        node_outbox:str  = "outbox_"+ node_id
        app.computing_nodes_db.create_collection(dump)
        app.computing_nodes_db.create_collection(node_inbox)
        app.computing_nodes_db.create_collection(node_outbox)

        response = {
            "status": "success",
            "message": "Node registered successfully",
            "node_id": new_node["node_id"],
        }


        return jsonify(response), 201

    except ValueError as e:
        abort(400, description=f"Invalid data format: {str(e)}")
    except Exception as e:
        abort(500, description=f"Server error: {str(e)}")

@worker_node_bp.errorhandler(400)
def bad_request(error):
    return {"status": "error", "message": str(error)}, 400

@worker_node_bp.errorhandler(500)
def server_error(error):
    return {"status": "error", "message": "Internal server error"}, 500

#COMPLETED
@worker_node_bp.route('/inbox/<string:node_id>', methods=['GET'])
def inbox(node_id: str):
    """
    This route handles GET requests to retrieve the number of tasks
    and requests for a particular node's inbox.
    """
    collection = f"inbox_{node_id}"

    app = cast(ExtendedFlask, current_app)

    try:
        nodes: list = app.computing_nodes_db.query_one_attribute("all_nodes", "node_id", node_id)
        if len(nodes) == 0:
            # If the node doesn't exist, respond with a 400 error
            abort(400, description='invalid node_id')

        # Query how many tasks are assigned
        num_tasks = app.computing_nodes_db.num_items_query(collection, {"status": "ASSIGNED"})

        # Query how many requests exist (indicated by the "data_request" field)
        num_requests = app.computing_nodes_db.num_items_query(collection, {"data_request": {"$exists": True}})
    except Exception as e:
        # If something goes wrong during the database queries, log or handle error
        app.logger.error(f"Database query failed for node_id={node_id}: {e}")
        abort(500, description='Internal Server Error')

    # Prepare the JSON response
    json_response = {
        "num_tasks": num_tasks,
        "num_requests": num_requests,
    }

    # Return the results as JSON with a 200 OK status
    return jsonify(json_response), 200

@worker_node_bp.route('/task/<string:node_id>', methods=['GET'])
def get_task(node_id: str):
    #TODO: worry about priority later. If a task has higher priority send it first.
    #For now just get a random task.


    app = cast(ExtendedFlask, current_app)
    collection = f"inbox_{node_id}"
    task: dict = app.computing_nodes_db.get_one(collection, {"status": {"$eq": "ASSIGNED"}})
    return jsonify(task)

@worker_node_bp.route('/data-request', methods=['GET'])
def get_data_request():
    #TODO: Implement this when we add advanced data collection on the nodes, such as battery life and network speed testing.

        return jsonify({})


#TODO
@worker_node_bp.route('/availability', methods=['PATCH'])
def change_availability():
    """
    Passes in a JSON containing 'node_id' and 'availability', updates that field in 'all_nodes'.
    For example:
      {
        "node_id": "...",
        "availability": false
      }
    """
    json_data = request.get_json()
    if not json_data or 'node_id' not in json_data:
        abort(400, description='Need to provide node_id')
    if 'availability' not in json_data:
        abort(400, description='Need to provide availability')

    node_id = json_data['node_id']
    availability_status = bool(json_data['availability'])

    print(node_id, "   ", availability_status)
    app = cast(ExtendedFlask, current_app)

    # This assumes you have a method called 'update_field' that updates a single field in a document.
    query = {"node_id": node_id}
    result = app.computing_nodes_db.update_field("all_nodes", query, "available", availability_status)

    #TODO:
    #Try to reassign all of the tasks to a new node.
    #if there is not a node available, put the task back in the unassigned_task box.
    #DONT FORGET TO CHANGE TASK DATA (WHO THE TASK IS ASSIGNED TO, RESET CRITICAL FIELDS LIKE DATE)
    #QUESTION: Procedure if it is in the middle of a task.
        #terminate task process (inside of the app)
        #change task status and try to reassign it.

    if result == 0:
        return jsonify({"status": "error", "message": "No matching node or nothing updated"}), 400

    #TODO
    #if the availability has changed from true to false:
        #1. gather all tasks in the inbox, move them to the unassigned category.
        #2. call a method that takes all the tasks in the unassigned category and assigns them to a node.

    return jsonify({
        "status": "success",
        "message": f"Availability for node '{node_id}' updated to {availability_status}"
    }), 200


# TODO: Make temporary usernames and passwords for uploading tasks.
# Current situation where I am passing around the connection string is really bad
@worker_node_bp.route('/outbox', methods=['POST'])
def outbox():
    #If it is a data request:
        #Gather results and put in dump.

    #if it is a task submission:
        #get the node id
        #get the task id --> find the  task in the node's inbox and remove it should be labeled processing
        #change the relevent fields of the dictionary.
        #repload it to the outbox category with the fields changed.

    """
    FIELDS TO CHANGE:
    'completed_at' --> get date
    ''
    'image_id' --> <task_id>.png
    'date_completed' --> get date


    """



    #if it is a data request, simply upload the data to the outbox.

    #if it is a task completion: upload all relevant parts of the task to the DB (links to the image, do this AFTER it has uploaded the image to the DB)


    #the Worker node will respond to the requests by publishing its answers here.
    # Includes: Network speed tests, battery life, results of tasks.
    return jsonify({"Nothing yet": "test for outbox"})


@worker_node_bp.route('/credentials', methods=['POST'])
def get_credentials():

    json_data = request.get_json()
    if not json_data or 'node_id' not in json_data:
        abort(400, description='Missing node_id')
    node_id = json_data['node_id']


    app = cast(ExtendedFlask, current_app)

    node = app.computing_nodes_db.query_one_attribute("all_nodes", "node_id", node_id)
    if not node:
        abort(400, description='Invalid or unavailable node_id')

    connection_string = os.getenv("NODE_MONGO_CONNECTION_STRING")

    return jsonify({
        "connection_string": connection_string,
    }), 200







