import pathlib
from tinydb import TinyDB, Query
import os
import json
import requests
import threading
import time
from typing import Dict, Any
from ..utils.logger import Logger
import logging
import win32pipe  # type: ignore # noqa: F401
import win32file  # type: ignore # noqa: F401
import pywintypes # type: ignore # noqa: F401


# Load configuration from config.json
config_data = json.loads((pathlib.Path(__file__).parent.parent.parent / "config.json").read_text())
logger = Logger(debug_file=config_data.get("debug_file", "app.log"))

class Pipe_Reader:
    data_object: TinyDB         = None
    pending_update: bool        = False
    last_output: dict[str,Any]  = None
    stream_timeout: int         = config_data.get("stream_timeout", 10)
    invalid_data_stream_timeout = None
    handle    = None
    
    def __init__(self, logger: bool = True, conf: Dict[str, Any] = None) -> None:
        if conf is not None:
            self.config = conf
        else:
            self.config = config_data
            
        if logger:
            logger = Logger(self.config.get("debug", False), 
                                 self.config.get("debug_file", "app.log"), 
                                 self.config.get("debug_level", "info"))
            
        # Initialize the data object Database
        self.data_object = TinyDB(os.path.join(os.path.dirname(__file__), f'{self.config["name"]}_DB.json'))
        self.entry = Query()
        
    @logger.log_debug(logging.INFO) 
    def check_version(self) -> None:
        """ Check for a new release """
        try:
            response = requests.get("https://github.com/repos/DarthGinger/Encyclopedia-Server/releases/latest")
            if response.status_code == 200:
                latest_version = response.json()["tag_name"]
                if latest_version and latest_version != config_data["version"]:
                    self.output_message("Encyclopedia Server version is out of date. Please update.")
                    self.pending_update = True
                else:
                    self.output_message("Encyclopedia Server is up to date.")
            else:
                self.output_message("Couldn't connect to Github for updates check.")
        except Exception as e:
            self.output_message(f"Error checking for updates: {str(e)}")
    
    @logger.log_debug(logging.DEBUG)    
    def data_feed(self) -> None:
        """ Read data from the data source """
        
        if self.config['data_source'] == 'pipe':
            self.read_from_pipe()
        else:
            self.read_from_file()
       
    @logger.log_debug(logging.DEBUG) 
    def read_from_pipe(self) -> None:
        try:
            pipe_name = self.config['pipe_name']
            buffer_size = int(self.config['buffer_size'])

            retry = 10
            while retry > 0:

                if self.handle is None:
                    self.handle = win32pipe.CreateNamedPipe(
                        pipe_name,
                        win32pipe.PIPE_ACCESS_DUPLEX,
                        win32pipe.PIPE_TYPE_MESSAGE | 
                        win32pipe.PIPE_READMODE_MESSAGE | 
                        win32pipe.PIPE_WAIT,
                        1, buffer_size, buffer_size, 0, None
                    )
                    print(f"Pipe handle created: {self.handle}")
                
                print(f"Waiting for connection on {pipe_name}...")
                win32pipe.ConnectNamedPipe(self.handle, None)
                win32pipe.SetNamedPipeHandleState(
                    self.handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
                
                
                print(f"Waiting for data on {pipe_name}...")
                data = win32file.ReadFile(self.handle, buffer_size)
                self.process_data(data.decode())
                print(f"Data received: {data}")
                    
        except pywintypes.error as e:
            if e.args[0] == 109:  # ERROR_BROKEN_PIPE
                print(f"Broken pipe: {str(e)}")
                retry -= 1
            elif e.args[0] == 2:  # No Pipe, retry
                print(f"No pipe: {str(e)}, retying {retry} times")
                retry -= 1
                time.sleep(2)
        except Exception as e:
            self.output_message(f"Pipe data stream not yet ready. Retrying... {str(e)}")
            time.sleep(2)
            self.read_from_pipe()
     
    @logger.log_debug(logging.DEBUG)       
    def read_from_file(self):
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class Watcher(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path == self.config['DEV_FILE_PATH']:
                    with open(event.src_path, 'r') as file:
                        data = file.read()
                        self.process_data(data)

        event_handler = Watcher()
        observer = Observer()
        observer.schedule(event_handler, path=self.config['DEV_FILE_PATH'], recursive=False)
        observer.start()
    
    def process_data(self, data: str):
        try:
            data = json.loads(data)
            self.data_object.upsert(data, data['id']==self.data_object.all()[0]['id'])
            
            self.output_message('Correct data stream received.', data)
            self.end_invalid_stream_timer()
            
        except json.JSONDecodeError:
            self.output_message('Invalid data stream format.')
            self.start_invalid_stream_timer()
            
        except Exception as e:
            self.output_message(f'Error processing data stream: {str(e)}')
            self.start_invalid_stream_timer()

    @logger.log_debug(logging.DEBUG)
    def output_message(self, message, data=None):
        if self.last_output != message:
            print(message)
            self.to_file(message, data) if self.config['to_file'] else None

            self.last_output = message

    @logger.log_debug(logging.CRITICAL)
    def to_file(self, message, data=None):
        with open(self.config['file_name'], 'a') as file:
            file.write("="*80 + '\n')
            file.write(message + '\n')
            
            if data is not None:
                file.write("="*80 + '\n')
                file.write(json.dumps(data) + '\n')
                
    @logger.log_debug(logging.WARNING)
    def start_invalid_stream_timer(self):
        if not self.invalid_data_stream_timeout:
            self.invalid_data_stream_timeout = threading.Timer(self.stream_timeout, self.clear_data_object)
            self.invalid_data_stream_timeout.start()

    @logger.log_debug(logging.WARNING)
    def end_invalid_stream_timer(self):
        if self.invalid_data_stream_timeout:
            self.invalid_data_stream_timeout.cancel()
            self.invalid_data_stream_timeout = None

    @logger.log_debug(logging.CRITICAL)
    def clear_data_object(self):
        self.data_object = None

    @logger.log_debug(logging.INFO)
    def start(self):
        self.output_message(f"X4 External App Server v{self.config["version"]}")
        while True:
            threading.Thread(target=self.data_feed, daemon=True).start()


if __name__ == '__main__':
    server = Pipe_Reader()
    server.start()