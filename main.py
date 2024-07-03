from app.pipe_reader.Pipe_Reader import Pipe_Reader
from app.utils.utils import parse_arguments, load_config, update_config_with_args
from app.utils.logger import Logger
import os

# Load default config from config.json
conf_path = os.path.join(os.path.dirname(__file__), "config.json")
config = load_config(conf_path)

# Parse command-line arguments
args = parse_arguments()

# Update config with command-line arguments
config = update_config_with_args(config, args)

# Create the Flask app



# Initialize the logger
# logger = Logger(app)

# hostname     : str         = app.config["host"]
# port         : int         = int(app.config["port"])
pipe_reader  : Pipe_Reader = Pipe_Reader()

if __name__ == "__main__":
    pipe_reader.start()