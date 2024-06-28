from flask import Flask, jsonify, current_app
import os
import json
import requests
from flask_cors import CORS
from flask_executor import Executor
import threading
import time
from typing import Dict, Any
from .logger import Logger
import logging
import win32pipe  # type: ignore # noqa: F401
import win32file  # type: ignore # noqa: F401
import pywintypes # type: ignore # noqa: F401

app = Flask(__name__)
CORS(app)
executor = Executor(app)

# Load configuration from config.json
with open(os.path.join(os.path.dirname(__file__), '..', 'config.json')) as config_file:
    config_data = json.load(config_file)
    
app.config.update(config_data)

hostname: str = app.config["host"]
port    : int = int(app.config["port"])
version : str = app.config["version"]

class Server:
    data_object: Dict[str, Any] = {}
    pending_update: bool        = False
    last_output: dict[str,Any]  = None
    stream_timeout: int         = app.config.get("stream_timeout", 10)
    invalid_data_stream_timeout = None
    
    def __init__(self, app, hostname: str, port: int, logger: Logger) -> None:
        self.app = app
        self.hostname = hostname
        self.port = port
        self.logger = logger
        
    @Logger.log_debug(logging.INFO) 
    def check_version(self) -> None:
        """ Check for a new release """
        try:
            response = requests.get("https://github.com/repos/DarthGinger/Encyclopedia-Server/releases/latest")
            if response.status_code == 200:
                latest_version = response.json()["tag_name"]
                if latest_version and latest_version != version:
                    self.output_message("Encyclopedia Server version is out of date. Please update.")
                    self.pending_update = True
                else:
                    self.output_message("Encyclopedia Server is up to date.")
            else:
                self.output_message("Couldn't connect to Github for updates check.")
        except Exception as e:
            self.output_message(f"Error checking for updates: {str(e)}")
    
    @Logger.log_debug(logging.DEBUG)        
    def serve(self) -> None:
        """ Serve the static files and start the server """
    
        @self.app.route("/")
        def index():
            return current_app.send_static_file("index.html")
        
        self.app.run(host=self.hostname, port=self.port, debug=self.app.config["debug"])
    
    @Logger.log_debug(logging.DEBUG)    
    def data_feed(self) -> None:
        """ Read data from the data source """
        
        if app.config['DATA_SOURCE'] == 'pipe':
            self.read_from_pipe()
        else:
            self.read_from_file()
       
    @Logger.log_debug(logging.DEBUG) 
    def read_from_pipe(self) -> None:
        try:
            pipe_name = app.config['pipe_name']
            buffer_size = int(app.config['buffer_size'])

            def read_pipe():
                while True:
                    try:
                        handle = win32file.CreateFile(
                            pipe_name,
                            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                            0,
                            None,
                            win32file.OPEN_EXISTING,
                            0,
                            None
                        )
                        
                        while True:
                            try:
                                data = win32file.ReadFile(handle, buffer_size)[1]
                                self.process_data(data.decode())
                            except pywintypes.error as e:
                                if e.args[0] == 109:  # ERROR_BROKEN_PIPE
                                    break
                                else:
                                    raise

                    except pywintypes.error as e:
                        self.output_message(f"Error reading from pipe: {str(e)}")
                        time.sleep(2)

            threading.Thread(target=read_pipe, daemon=True).start()
        except Exception as e:
            self.output_message(f"Pipe data stream not yet ready. Retrying... {str(e)}")
            time.sleep(2)
            self.read_from_pipe()
     
    @Logger.log_debug(logging.DEBUG)       
    def read_from_file(self):
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class Watcher(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path == app.config['DEV_FILE_PATH']:
                    with open(event.src_path, 'r') as file:
                        data = file.read()
                        self.process_data(data)

        event_handler = Watcher()
        observer = Observer()
        observer.schedule(event_handler, path=app.config['DEV_FILE_PATH'], recursive=False)
        observer.start()
    
    def process_data(self, data: str):
        try:
            self.data_object = json.loads(data)
            self.output_message('Correct data stream received.')
            self.end_invalid_stream_timer()
        except json.JSONDecodeError:
            self.output_message('Invalid data stream format.')
            self.start_invalid_stream_timer()

    @Logger.log_debug(logging.DEBUG)
    def set_api(self):
        """
        Set up the API route for '/api/data' with the GET method.

        This function sets up the API route '/api/data' with the GET method. When a GET request is made to this route, 
        the function checks if the `data_object` attribute of the current instance is not None. If it is not None, it 
        adds the value of the `update_pending` attribute to the `data_object` dictionary with the key 'update_pending'. 
        Finally, it returns the `data_object` dictionary as a JSON response.

        Parameters:
        - self: The current instance of the class.

        Returns:
        - A JSON response containing the `data_object` dictionary.
        """
        @self.app.route('/api/data', methods=['GET'])
        def get_data():
            if self.data_object:
                self.data_object['update_pending'] = self.update_pending
            return jsonify(self.data_object)

    @Logger.log_debug(logging.DEBUG)
    def output_message(self, message):
        if self.last_output_message != message:
            print(message)
            if self.app.config['to_file']:
                with open(self.app.config['file_name'], 'a') as file:
                    file.write(message + '\n')
            self.last_output_message = message

    @Logger.log_debug(logging.DEBUG)
    def start_invalid_stream_timer(self):
        if not self.invalid_data_stream_timeout:
            self.invalid_data_stream_timeout = threading.Timer(self.stream_timeout, self.clear_data_object)
            self.invalid_data_stream_timeout.start()

    @Logger.log_debug(logging.DEBUG)
    def end_invalid_stream_timer(self):
        if self.invalid_data_stream_timeout:
            self.invalid_data_stream_timeout.cancel()
            self.invalid_data_stream_timeout = None

    @Logger.log_debug(logging.DEBUG)
    def clear_data_object(self):
        self.data_object = None

    @Logger.log_debug(logging.INFO)
    def start(self):
        self.output_message(f"X4 External App Server v{version}")
        threading.Thread(target=self.serve, daemon=True).start()
        executor.submit(self.check_version)
        self.set_api()
        self.output_message('')
        self.data_feed()

if __name__ == '__main__':
    server = Server(app, hostname, port)
    server.start()