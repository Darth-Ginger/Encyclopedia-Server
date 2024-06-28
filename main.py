from app import create_app
from app.server import Server
from app.utils import parse_arguments, load_config, update_config_with_args
from app.logger import Logger
import os

# Load default config from config.json
conf_path = os.path.join(os.path.dirname(__file__), "config.json")
config = load_config(conf_path)

# Parse command-line arguments
args = parse_arguments()

# Update config with command-line arguments
config = update_config_with_args(config, args)

# Create the Flask app
app = create_app()
app.config.update(config)

# Initialize the logger
logger = Logger(app)

hostname: str    = app.config["host"]
port    : int    = int(app.config["port"])
server  : Server = Server(hostname=hostname, port=port)

if __name__ == "__main__":
    server.start()