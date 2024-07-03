# app/logger.py

import logging

log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

class Logger:
    def __init__(self, debug=False, debug_file='app.log', debug_level='info'):
        self.debug = debug
        self.debug_file = debug_file
        self.debug_level = log_levels.get(debug_level, logging.INFO)

        if self.debug:
            logging.basicConfig(
                filename=self.debug_file,
                level=self.debug_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        self.logger = logging.getLogger(__name__)

    def log_debug(self, level):
        """
        Decorator to log function calls based on the debug level.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                func_logger = None
                if hasattr(func, '__self__') and hasattr(func.__self__, 'logger'):
                    func_logger = getattr(func.__self__, 'logger', None)
                
                if func_logger and func_logger.debug_level <= level:
                    func_logger.log(level, f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
                else:
                    self.logger.log(level, f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
