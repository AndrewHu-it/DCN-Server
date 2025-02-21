# app/extended_flask.py
from flask import Flask
from app.utilities.database import DataBase

class ExtendedFlask(Flask):
    # Declare custom attributes so that type checkers recognize them
    jobs_and_tasks_db: DataBase
    computing_nodes_db: DataBase
