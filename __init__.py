from .node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .routes import setup_routes
import os

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]


def setup(app):
    setup_routes(app)
