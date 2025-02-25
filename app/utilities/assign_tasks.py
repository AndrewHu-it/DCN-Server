import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, abort, current_app
from typing import cast
from app.extended_flask import ExtendedFlask
import sys

#This is the algorithm that I will work on extensively with ML regression of node performance etc later on.


def assign_task(task_id: str):
    app = cast(ExtendedFlask, current_app)
    task_to_assign: dict = app.jobs_and_tasks_db.find_and_delete("unassigned_tasks", {"task_id": task_id})[0]

    node_id = node_id_to_assign(task_to_assign['task_id'])

    if node_id is None:
        app.jobs_and_tasks_db.add("unassigned_tasks", task_to_assign)
        print("no available nodes")
        return "no available nodes"


    collection = str("inbox_" + node_id)
    task_to_assign['assigned_to'] = node_id
    task_to_assign['status'] = "ASSIGNED"
    task_to_assign['assigned_at'] = {"$date": datetime.utcnow().isoformat() + "Z"}
    #update the job field.
    job_id = task_to_assign['job_id']
    app.jobs_and_tasks_db.update_field('active_jobs', {"job_id": job_id}, f"tasks_and_nodes.{task_id}", node_id)
    app.jobs_and_tasks_db.update_field('active_jobs', {"job_id": job_id}, "status", "TASKS-ASSIGNED")


    app.computing_nodes_db.add(collection, task_to_assign)
    return "success"


def node_id_to_assign(task_id: str) -> str:
    app = cast(ExtendedFlask, current_app)
    active_nodes = app.computing_nodes_db.query_one_attribute("all_nodes", "available", True)

    min_tasks = sys.maxsize
    min_node_id = None
    for node in active_nodes:
        current_node_id = node["node_id"]
        current_node_inbox_size = app.computing_nodes_db.collection_size(str("inbox_" + current_node_id))
        if current_node_inbox_size < min_tasks:
            min_tasks = current_node_inbox_size
            min_node_id = current_node_id

    return min_node_id





