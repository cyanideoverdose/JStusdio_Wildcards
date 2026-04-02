from .node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .routes import setup_routes
import os
 
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")
 
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
 
try:
    from server import PromptServer
    setup_routes(PromptServer.instance.app)
    print("[JStudio Wildcards] Routes registered.")
except Exception as e:
    print(f"[JStudio Wildcards] WARNING: Could not register routes: {e}")
 