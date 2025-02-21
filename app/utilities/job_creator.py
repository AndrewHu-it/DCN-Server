import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


def generate_tasks(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    width: int,
    height: int,
    num_tasks: int,
    job_id: str,
    priority: str
) -> List[Dict[str, Any]]:
    """
    Divides the Mandelbrot set region into 'num_tasks' vertical slices, each covering a stripe of the full y-range.

    Args:
        x_min (float): Minimum x-coordinate (real axis) of the region.
        x_max (float): Maximum x-coordinate (real axis) of the region.
        y_min (float): Minimum y-coordinate (imaginary axis) of the region.
        y_max (float): Maximum y-coordinate (imaginary axis) of the region.
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        num_tasks (int): Number of tasks to split the job into.
        job_id (str): Unique identifier of the parent job.
        priority (str): Priority level of the tasks (e.g., "LOW", "HIGH").

    Returns:
        List[Dict[str, Any]]: List of task dictionaries, each defining a slice of the Mandelbrot set.

    Raises:
        ValueError: If num_tasks is less than 1 or exceeds width * height.
    """
    if num_tasks < 1:
        raise ValueError("num_tasks must be at least 1")
    if num_tasks > width * height:
        raise ValueError(f"num_tasks ({num_tasks}) cannot exceed total pixels ({width * height})")

    tasks = []
    x_range = x_max - x_min
    x_step = x_range / num_tasks

    for i in range(num_tasks):
        task_x_min = x_min + i * x_step
        task_x_max = x_min + (i + 1) * x_step if i < num_tasks - 1 else x_max

        pixel_x_min = (width * i) // num_tasks
        pixel_x_max = (width * (i + 1)) // num_tasks  # One past the last pixel column
        task_width = pixel_x_max - pixel_x_min

        task = {
            "task_id": str(uuid.uuid4()),
            "job_id": job_id,
            "time_created": {"$date": datetime.utcnow().isoformat() + "Z"},  # UTC with 'Z' for consistency
            "status": "AVAILABLE",
            "assigned_to": None,
            "assigned_at": {"$date": None},
            "completed_at": {"$date": None},
            "instruction": "MANDELBROT",  # Placeholder; consider an enum or config in production
            "instruction_data": {
                "x_min": task_x_min,
                "x_max": task_x_max,
                "y_min": y_min,
                "y_max": y_max,
                "width": task_width,
                "height": height
            },
            "priority": priority,
            "output_data": {
                "image_id": None,
                "storage_method": "GridFS",
                "file_name": None
            },
            "image_metadata": {
                "resolution": f"{width}x{height}",
                "color_depth": "24-bit",
                "compression": "PNG"
            }
        }
        tasks.append(task)

    return tasks


def create_job_and_tasks(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    width: int,
    height: int,
    client_id: str,
    *,
    num_tasks: int = 16,
    message: str = "Default Message",
    priority: str = "LOW"
) -> List[Any]:
    """
    Creates a job and its associated tasks for rendering a Mandelbrot set region.

    Args:
        x_min (float): Minimum x-coordinate (real axis) of the region.
        x_max (float): Maximum x-coordinate (real axis) of the region.
        y_min (float): Minimum y-coordinate (imaginary axis) of the region.
        y_max (float): Maximum y-coordinate (imaginary axis) of the region.
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        client_id (str): Identifier of the client submitting the job.
        num_tasks (int, optional): Number of tasks to split the job into. Defaults to 16.
        message (str, optional): Description of the job. Defaults to "Default Message".
        priority (str, optional): Priority level of the job. Defaults to "LOW".

    Returns:
        List[Any]: A list where:
            - First item is a dict representing the job.
            - Remaining items are a list of task dicts associated with the job.

    Raises:
        ValueError: If num_tasks is invalid or region dimensions are inconsistent.
    """
    if x_max <= x_min or y_max <= y_min:
        raise ValueError("Invalid region: x_max must be greater than x_min, and y_max must be greater than y_min")
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive integers")

    job_id = str(uuid.uuid4())
    tasks = generate_tasks(x_min, x_max, y_min, y_max, width, height, num_tasks, job_id, priority)
    task_ids = [task["task_id"] for task in tasks]  # Extract task IDs for the job

    job = {
        "job_id": job_id,
        "job_description": message,
        "status": "NOT-STARTED",
        "created_at": {"$date": datetime.utcnow().isoformat() + "Z"},  # UTC with 'Z'
        "completed_at": None,
        "num_tasks": num_tasks,
        "mandelbrot": {
            "region": {
                "x_min": x_min,
                "x_max": x_max,
                "y_min": y_min,
                "y_max": y_max
            },
            "resolution": {
                "width": width,
                "height": height
            }
        },
        "tasks": task_ids,  # List of actual task IDs
        "owner": client_id,
        "priority": priority
    }

    return [job] + tasks  # Return job as first item, followed by tasks


# No testing code included for production readiness