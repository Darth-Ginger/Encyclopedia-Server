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
        self.debug      : bool = app.config.get('debug', False)
        self.debug_file : str  = app.config.get('debug_file', 'app.log')
        self.debug_level: int  = log_levels.get(app.config.get('debug_level', "info"))

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
                func_logger = None
                if hasattr(func.__self__.__class__, 'logger'):
                    func_logger: Logger = func.__self__.__class__.logger
                if func_logger is not None \
                    and func_logger.debug_level <= level:
                    current_app.logger.log(level, f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
