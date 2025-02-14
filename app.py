
from flask import Flask
from routes.getinfo import *

app = Flask(__name__)

# main driver function
if __name__ == '__main__':
    app.run()