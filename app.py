import os

from flask import Flask
# now we have to import the blueprints:
from routes.index import index_bp
from routes.api import api_bp

# initialize the application:
app = Flask(__name__)

app.register_blueprint(index_bp)
app.register_blueprint(api_bp)

if __name__ == '__main__':
    port = 8080
    app.run(host='0.0.0.0', port=port)