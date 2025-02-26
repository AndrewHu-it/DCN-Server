# app/extended_flask.py
from flask import Flask
from app.utilities.database import DataBase

class ExtendedFlask(Flask):
    jobs_and_tasks_db: DataBase
    computing_nodes_db: DataBase
