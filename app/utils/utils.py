import os
from typing import Any, Dict
from argparse import ArgumentParser, HelpFormatter
import json


conf_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')

with open(conf_file, 'r') as config_file:
    config = json.load(config_file)

class CustomHelpFormatter(HelpFormatter):
    def __init__(self, prog: str) -> None:
        super(CustomHelpFormatter, self).__init__(prog, max_help_position=80)
        

def parse_arguments() -> Dict[str, Any]:
    """
    Parse command-line arguments and return them as a dictionary.
    """
    base_parser = ArgumentParser(
        prog="External Encyclopedia Server",
        description="External Encyclopedia Server for X4",
        add_help=False,
        formatter_class=CustomHelpFormatter
    )
        
    base_parser.add_argument("-?", "--help", action="help", 
                             help="Show this help message and exit.")
    base_parser.add_argument("-h","--host", type=str, default=config.get("host", "127.0.0.1"),
                             help=f"Host to run the server on. Default: {config.get("host", "127.0.0.1")}")
    base_parser.add_argument("-p", "--port", type=int, default=config.get("port", 5000),
                             help=f"Port to run the server on. Default: {config.get("port", 5000)}")
    base_parser.add_argument("-t", "--stream_timeout", type=int, default=config.get("stream_timeout", 10),
                             help=f"Stream timeout in seconds. Default: {config.get('stream_timeout', "10")}")
    base_parser.add_argument("-src", "--data_source", type=str, default=config.get('data_source', 'pipe'),
                             help=f"Data source. Default: {config.get('data_source', 'pipe')}")
    base_parser.add_argument("-d", "--debug", type=bool, default=config.get("debug", False),
                             help=f"Debug mode. Default: {config.get("debug", "False")}")
    base_parser.add_argument("-pipe", "--pipe_name", type=str, default=config.get("pipe_name", "\\.\\pipe\\x4_external_encyclopedia"),
                             help=f"Pipe name. Default: {config.get("pipe_name", "\\.\\pipe\\x4_external_encyclopedia")}")
    base_parser.add_argument("-b", "--buffer_size", type=int, default=config.get("buffer_size", 2048),
                             help=f"Buffer size. Default: {config.get("buffer_size", 2048)}")
    
    args = base_parser.parse_args()
    
    args_dict = {k: v for k, v in vars(args).items() if v is not None}
    
    return args_dict

def load_config(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    """
    with open(file_path) as config_file:
        return json.load(config_file)

def update_config_with_args(config: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the configuration dictionary with command-line arguments.
    """
    config.update(args)
    return config


    