from .server import app, Server
from .logger import Logger
from flask import Flask


__all__ = ["Server", "Logger"]

def create_app() -> Flask:
    return app