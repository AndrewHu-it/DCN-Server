import sys
import uuid
from datetime import datetime


def generate_tasks(x_min: float, x_max: float, y_min: float, y_max: float,
                   width: int, height: int, num_tasks: int, job_id: str, priority: str) -> list:
    """
    Divides the Mandelbrot set region specified by (x_min, x_max, y_min, y_max) and image dimensions (width, height)
    into 'num_tasks' vertical slices. Each task covers a vertical stripe of the full y-range.

    The coordinate boundaries (x_min, x_max) are split evenly in floating point, while the pixel columns
    are partitioned using integer arithmetic to ensure every pixel is assigned without overlap or gaps.
    """
    list_of_tasks = []

    x_range = x_max - x_min
    x_step = x_range / num_tasks

    for i in range(num_tasks):
        task_x_min = x_min + i * x_step
        task_x_max = x_min + (i + 1) * x_step if i < num_tasks - 1 else x_max


        pixel_x_min = (width * i) // num_tasks
        pixel_x_max = (width * (i + 1)) // num_tasks  # This is one past the last pixel column for the task.

        task_width = pixel_x_max - pixel_x_min

        task_y_min = y_min
        task_y_max = y_max
        task_height = height  # Full height of the image


        # Modify parameters later.
        task = {
            "task_id": str(uuid.uuid4()),
            "job_id": job_id,
            "time_created": {"$date": datetime.now().isoformat()},
            "status": "AVAILABLE",
            "assigned_to": None,
            "assigned_at": {"$date": None},
            "completed_at": {"$date": None},
            "instruction": "FIBO",  # Placeholder instruction; can be replaced as needed.
            "instruction_data": {
                "x_min": task_x_min,  # Left boundary in coordinate space.
                "x_max": task_x_max,  # Right boundary in coordinate space.
                "y_min": task_y_min,  # Lower boundary in coordinate space.
                "y_max": task_y_max,  # Upper boundary in coordinate space.
                "width": task_width,  # Number of pixel columns for this task.
                "height": task_height  # Total number of pixel rows (unchanged).
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

        list_of_tasks.append(task)

    return list_of_tasks


def create_job_and_tasks(x_min: float, x_max: float, y_min: float, y_max: float, width: int,
                         height: int, client_id: str, *, num_tasks: int = 16, message: str = "Default Message", priority: str = "LOW") -> list:
    """
       Parameters:
          x_min (float): The minimum x-coordinate (real axis) for the Mandelbrot set region.
          x_max (float): The maximum x-coordinate (real axis) for the Mandelbrot set region.
          y_min (float): The minimum y-coordinate (imaginary axis) for the Mandelbrot set region.
          y_max (float): The maximum y-coordinate (imaginary axis) for the Mandelbrot set region.
          width (int): The width of the output image in pixels.
          height (int): The height of the output image in pixels.
          num_tasks (int): The number of tasks to create.
          message (str, optional): The default message to use. Defaults to "Default Message".
          client_id (str, optional): The client id of the job. Defaults to "Job Creator".
          priority (str, optional): The priority of the job. Defaults to "LOW".

      Output:
        Returns a list:
            First item is a dictionary that represents the JOB that has just been created
            Second item is a LIST:
                List contains the TASKS associated with the JOB
    """

    job: dict = {}
    this_job_id = str(uuid.uuid4())
    tasks: list = generate_tasks(x_min, x_max, y_min, y_max, width, height, num_tasks, this_job_id, priority)



    job = {
        "job_id": this_job_id,
        "job_description": message,
        "status": "NOT-STARTED",
        "created_at": {"$date": datetime.now().isoformat()},
        "completed at": None,
        "num_tasks": num_tasks,
        "mandelbrot": {
            "region": {
                "x_min": x_min,
                "x_max": x_max,
                "y_min": y_min,
                "y_max": y_max,
            },
            "resolution": {
                "width": width,
                "height": height
            }
        },
        "tasks": [
            "unique_task_id_1",
            "unique_task_id_2",
            "unique_task_id_3"
        ],
        "owner": client_id,
        "priority": priority,
    }


    return [job, tasks]




# These methods are used for TESTING ONLY. DELETE BEFORE PRODUCTION:
#_ ____. ________#_ ____. ________#_ ____. ________#_ ____. ________#_ ____. ________
def main():
    # Default values.
    x_min = -1.5
    x_max = 1.5
    y_min = -1.5
    y_max = 1.5
    width: int = 1000
    height: int = 1000
    number_of_tasks: int = 16
    client_id: str = "Job Creator"
    priority: str = "LOW"


    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-x' and i + 1 < len(sys.argv):
            width = int(sys.argv[i + 1])
            i+= 2
        elif sys.argv[i] == '-y' and i + 1 < len(sys.argv):
            height = int(sys.argv[i + 1])
            i += 2
        elif (sys.argv[i] == '--tasks' or sys.argv[i] == '-t') and i + 1 < len(sys.argv):
            number_of_tasks = int(sys.argv[i + 1])
            i += 2
        elif ( sys.argv[i] == '--client-id') and i + 1 < len(sys.argv):
            client_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '-xmin' and i + 1 < len(sys.argv):
            x_min = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '-ymin' and i + 1 < len(sys.argv):
            y_min = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '-ymax' and i + 1 < len(sys.argv):
            y_max = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '-xmax' and i + 1 < len(sys.argv):
            x_max = float(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    # Ensure correct parameters:
    if number_of_tasks >width*height:
        number_of_tasks = width*height

    job_task: list = create_job_and_tasks(x_min, x_max, y_min, y_max, width, height, client_id, priority=priority, num_tasks=number_of_tasks)

    print(job_task[0])
    for x in job_task[1]:
        print(x)

    print("{} by {} with {} tasks".format(width, height, number_of_tasks))


if __name__ == "__main__":
    main()


