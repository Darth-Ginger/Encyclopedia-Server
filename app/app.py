from .utils.logger import Logger
from flask import Flask, jsonify, current_app
import os
import json
import requests
from flask_cors import CORS
from flask_executor import Executor
import threading
import time
from typing import Dict, Any

# Load configuration from config.json
with open(os.path.join(os.path.dirname(__file__), '..', 'config.json')) as config_file:
    config_data = json.load(config_file)

app = Flask(config_data["name"])
CORS(app)
executor = Executor(app)

app.config.update(config_data)

hostname: str = app.config["host"]
port    : int = int(app.config["port"])
version : str = app.config["version"]