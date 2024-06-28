# app/logger.py

import logging

from flask import current_app

log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

class Logger:
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app) -> None:
        """
        Initialize the logger based on the application's configuration.
        """
        self.debug = app.config.get('debug', False)
        self.debug_file = app.config.get('debug_file', 'app.log')
        self.debug_level = log_levels.get(app.config.get('debug_level', "info"))

        if self.debug:
            logging.basicConfig(
                filename=self.debug_file,
                level=self.debug_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    @staticmethod
    def log_debug(level) -> None:
        """
        Decorator to log function calls based on the debug level.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                if current_app.config.get('DEBUG', False) and current_app.config.get('DEBUG_LEVEL', logging.DEBUG) <= level:
                    current_app.logger.log(level, f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
