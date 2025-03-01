import mimetypes
from datetime import datetime

import gridfs
from flask import Blueprint, request, jsonify, abort, current_app, Response
from typing import cast
from app.extended_flask import ExtendedFlask
from ..utilities.job_creator import create_job_and_tasks
from ..utilities.assign_tasks import assign_task
from PIL import Image  # Make sure Pillow is installed
from io import BytesIO



client_bp = Blueprint('client_bp', __name__, url_prefix='/client')


@client_bp.route('/job', methods=['POST'])
def upload_job():

    json_data = request.get_json()
    if not json_data or 'client_id' not in json_data:
        abort(400, description='Missing client_id')

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

        job: dict = jobs_and_tasks[0]
        tasks: list = jobs_and_tasks[1:]

        # have to recast the app
        app = cast(ExtendedFlask, current_app)
        job_result = app.jobs_and_tasks_db.add("active_jobs", job)
        job["_id"] = str(job_result.inserted_id)

        #insert into unassigned
        for task in tasks:
            task_result = app.jobs_and_tasks_db.add("unassigned_tasks", task)
            task["_id"] = str(task_result.inserted_id)


        #now that they are in the available collection we query that collection to assign all nodes in it.
        all_unassigned_tasks = app.jobs_and_tasks_db.get_all("unassigned_tasks")
        for task in all_unassigned_tasks:
            task_id = task["task_id"]
            assign_task(task_id)


        return_json: dict = {
            "job_id": job["job_id"],
            "client_id": job["client_id"],
            "priority": job["priority"],
        }


        return jsonify(return_json), 201

    except ValueError as e:
        abort(400, description=str(e))
    except Exception as e:
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



@client_bp.route('/completed-job/<job_id>', methods=['GET'])
def download_and_reconstruct_job(job_id: str):
    """Reconstruct a completed Mandelbrot job by assembling partial slices from each node's outbox."""
    # 1) Basic Setup: Retrieve the Job
    app = cast(ExtendedFlask, current_app)
    job_db = app.jobs_and_tasks_db

    job_query = {"job_id": job_id}
    job_doc = job_db.get_one("active_jobs", job_query)
    if not job_doc:
        abort(404, description=f"No job found with job_id={job_id}")

    # 2) Extract High-Level Job Info
    total_tasks = job_doc["num_tasks"]
    mandelbrot_info = job_doc["mandelbrot"]
    x_min = mandelbrot_info["region"]["x_min"]
    x_max = mandelbrot_info["region"]["x_max"]
    y_min = mandelbrot_info["region"]["y_min"]
    y_max = mandelbrot_info["region"]["y_max"]
    final_width = mandelbrot_info["resolution"]["width"]
    final_height = mandelbrot_info["resolution"]["height"]

    tasks_and_nodes = job_doc["tasks_and_nodes"]  # e.g. {task_id: node_id, ...}

    # 3) Verify Completion in Each Node's Outbox
    computing_nodes_db = app.computing_nodes_db  # Database handle for computing nodes
    completed_tasks = []
    for task_id, node_id in tasks_and_nodes.items():
        outbox_collection = f"outbox_{node_id}"
        outbox_doc = computing_nodes_db.get_one(
            outbox_collection,
            {"task_id": task_id, "job_id": job_id}
            #also add a consrtaint later about task being completed or to::: "status": "COMPLETED"
        )
        if not outbox_doc:
            abort(400, description=(
                f"Job {job_id} not fully completed: "
                f"Missing or incomplete task {task_id} in node {node_id}'s outbox."
            ))
        completed_tasks.append(outbox_doc)


    if len(completed_tasks) < total_tasks:
        abort(400, description=(
            f"Job {job_id} is not fully completed. "
            f"Found {len(completed_tasks)}/{total_tasks} tasks marked COMPLETED in node outboxes."
        ))



    x_total_range = x_max - x_min
    tasks_db = app.jobs_and_tasks_db
    tasks_info = []

    for task in completed_tasks:

        instr_data = task["instruction_data"]
        x_min_slice = float(instr_data["x_min"])
        x_max_slice = float(instr_data["x_max"])
        tasks_info.append({
            "task_id": task["task_id"],
            "node_id": task["assigned_to"],
            "x_min": x_min_slice,
            "x_max": x_max_slice,
            "width": instr_data["width"],
            "height": instr_data["height"],
        })

    # Sort tasks by x_min so we paste them in the correct horizontal order
    tasks_info.sort(key=lambda t: t["x_min"])



    # 5) Reconstruct the Final Image
    final_image = Image.new("RGB", (final_width, final_height))
    for task_data in tasks_info:
        partial_file = job_db.get_file_gridfs(task_data["task_id"])
        if not partial_file:
            abort(404, description=f"Missing partial image in GridFS for task {task_data['task_id']}")

        partial_bytes = BytesIO(partial_file.read())
        partial_img = Image.open(partial_bytes).convert("RGB")

        # Compute the horizontal offset for this slice
        offset_x = int(round((task_data["x_min"] - x_min) / x_total_range * final_width))
        offset_y = 0  # We only slice horizontally; the Y range is the entire image

        final_image.paste(partial_img, (offset_x, offset_y))
        partial_img.close()
        partial_file.close()


    #right here we can set the relevant fields.
    #def update_field(self, collection: str, query: dict, field: str, value: any) -> int:


    query_jobs = {"job_id": job_id}
    job_db.update_field("active_jobs", query_jobs, "status", "COMPLETED")
    job_db.update_field("active_jobs", query_jobs, "completed_at", {"$date": datetime.utcnow().isoformat() + "Z"})


    output_buffer = BytesIO()
    final_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return Response(output_buffer.getvalue(), mimetype="image/png")


@client_bp.route('/task-result/<task_id>', methods=['GET'])
def download_image(task_id: str):
    """Stream an image from GridFS back to the client without loading it all into memory."""
    app = cast(ExtendedFlask, current_app)

    # 1) Get the database reference and retrieve the GridFS file
    db = app.jobs_and_tasks_db
    grid_out = db.get_file_gridfs(task_id)
    if not grid_out:
        abort(404, description="No image found for the specified task_id in GridFS.")

    # 2) Determine the content type
    content_type = getattr(grid_out, 'contentType', None)
    if not content_type:
        content_type = mimetypes.guess_type(grid_out.filename or '')[0] or 'application/octet-stream'

    # 3) Important: Seek to the start of the file, just to be sure
    #    (especially if something has read from it earlier)
    grid_out.seek(0)

    # 4) Create a generator function to yield chunks of data
    def generate_chunks(file_obj, chunk_size=8192):
        while True:
            data = file_obj.read(chunk_size)
            if not data:
                break
            yield data



    # 5) Return a streaming response
    return Response(
        generate_chunks(grid_out),
        mimetype=content_type,
        # Optional: set a filename if you want the browser to download it
        # headers={"Content-Disposition": f"attachment; filename={grid_out.filename}"}
    )







