from app.extended_flask import ExtendedFlask
from config import Config
from app.routes.client import client_bp
from app.routes.worker_node import worker_node_bp
from app.routes.main import main_bp
from app.utilities.database import DataBase
import os

connection_string = os.getenv("MONGO_CONNECTION_STRING")
dbs = ["jobs_and_tasks", "computing_nodes"]


def create_app(config_class=Config) -> ExtendedFlask:
    # Instantiate our subclass instead of plain Flask
    app = ExtendedFlask(__name__)
    app.config.from_object(config_class)

    # Attach DB instances to the ExtendedFlask object
    app.jobs_and_tasks_db = DataBase(connection_string, dbs[0])
    app.computing_nodes_db = DataBase(connection_string, dbs[1])

    # Register blueprints (ensure 'client_bp' is imported after ExtendedFlask is defined)
    from app.routes.client import client_bp
    from app.routes.worker_node import worker_node_bp
    from app.routes.main import main_bp
    app.register_blueprint(client_bp)
    app.register_blueprint(worker_node_bp)
    app.register_blueprint(main_bp)

    return app