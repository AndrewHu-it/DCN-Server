import mimetypes

import gridfs
from flask import Blueprint, request, jsonify, abort, current_app, Response
from typing import cast
from app.extended_flask import ExtendedFlask
from ..utilities.job_creator import create_job_and_tasks
from ..utilities.assign_tasks import assign_task


# Create the blueprint for client-related routes
client_bp = Blueprint('client_bp', __name__, url_prefix='/client')


@client_bp.route('/job', methods=['POST'])
def upload_job():
    """
    Handle POST requests to create a new job and its associated tasks.
    Expects JSON data with client details, job specifics, and Mandelbrot set parameters.
    """
    # Parse and validate incoming JSON data
    json_data = request.get_json()
    if not json_data or 'client_id' not in json_data:
        abort(400, description='Missing client_id')

    # Extract required and optional fields from JSON
    client_id: str = json_data['client_id']
    job_description: str = json_data.get('job_description', 'No Description Provided')
    priority: str = json_data.get('priority', 'low')

    mandelbrot = json_data.get('mandelbrot', {})
    region = mandelbrot.get('region', {})
    x_min: float = float(region.get('x_min', -2.0))
    x_max: float = float(region.get('x_max', 1.0))
    y_min: float = float(region.get('y_min', -1.5))
    y_max: float = float(region.get('y_max', 1.5))

    resolution = mandelbrot.get('resolution', {})
    x_resolution: int = int(resolution.get('x_resolution', 3840))
    y_resolution: int = int(resolution.get('y_resolution', 2160))
    num_tasks: int = int(json_data.get('num_tasks', 16))

    try:
        # Create job and tasks using the utility function
        jobs_and_tasks = create_job_and_tasks(
            x_min, x_max, y_min, y_max,
            x_resolution, y_resolution,
            client_id,
            num_tasks=num_tasks,
            message=job_description,
            priority=priority
        )

        # Extract job and tasks from the returned list
        job: dict = jobs_and_tasks[0]
        tasks: list = jobs_and_tasks[1:]

        # Access the database via the extended Flask app
        app = cast(ExtendedFlask, current_app)

        # Insert the job into the "active_jobs" collection
        job_result = app.jobs_and_tasks_db.add("active_jobs", job)
        job["_id"] = str(job_result.inserted_id)



        # Insert each task into the "unassigned_tasks" collection
        for task in tasks:
            task_result = app.jobs_and_tasks_db.add("unassigned_tasks", task)
            task["_id"] = str(task_result.inserted_id)


        #now that they are in the available collection we query that collection to assign all nodes in it.
        all_unassigned_tasks = app.jobs_and_tasks_db.get_all("unassigned_tasks")
        for task in all_unassigned_tasks:
            task_id = task["task_id"]
            assign_task(task_id)


        # Return the job details with a 201 status code (Created)
        return_json: dict = {
            "job_id": job["job_id"],
            "client_id": job["client_id"],
            "priority": job["priority"],
        }


        return jsonify(return_json), 201

    except ValueError as e:
        # Handle invalid inputs from create_job_and_tasks
        abort(400, description=str(e))
    except Exception as e:
        # Handle general server errors, such as database issues
        abort(500, description=f"Server error: {str(e)}")


@client_bp.route('/job/<job_id>', methods=['GET'])
def get_job(job_id):
    """
    Handle GET requests to retrieve a job by its ID.
    Returns the job details if found, or a 404 error if not.


    """

    app = cast(ExtendedFlask, current_app)
    job = app.jobs_and_tasks_db.query_one_attribute("active_jobs", "job_id", str(job_id))

    if job:
        return jsonify(job)
    else:
        abort(404, description="Job not found")

@client_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id):

    #TODO:
    #WARNING:This might be a little more complicated because tasks could be in either the node they are assigned to or in the active jobs category.
    ####WARNING.

    app = cast(ExtendedFlask, current_app)
    task = app.jobs_and_tasks_db.query_one_attribute("unassigned_tasks", "task_id", str(task_id))
    if task:
        return jsonify(task)
    else:
        abort(404, description="Task not found")



#Might want to create an endpoint to view an individual task as well.


@client_bp.route('/task-result/<task_id>', methods=['GET'])
def download_image(task_id: str):
    # probably should first check that the task is complete.
    print(task_id)

    app = cast(ExtendedFlask, current_app)

    db = app.jobs_and_tasks_db
    grid_out = db.get_file_gridfs(task_id)
    if not grid_out:
        abort(404, description="No image found for the specified task_id in GridFS.")

        # Derive MIME type
    content_type = getattr(grid_out, 'contentType', None)
    if not content_type:
        # Attempt to guess from filename or default to 'image/png'
        content_type = mimetypes.guess_type(grid_out.filename or '')[0] or 'image/png'

    # Read entire file into memory; for large files, consider streaming
    file_data = grid_out.read()

    # Return as HTTP response
    return Response(file_data, mimetype=content_type)





