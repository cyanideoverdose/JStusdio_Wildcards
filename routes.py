from aiohttp import web
from .node import reload_wildcards, _get_wildcards_folder
import os


async def reload_wildcards_handler(request):
    reload_wildcards()
    count = 0
    folder = _get_wildcards_folder()
    if folder and os.path.isdir(folder):
        for root, dirs, files in os.walk(folder):
            count += sum(1 for f in files if f.endswith((".txt", ".yaml", ".yml")))
    msg = f"Reloaded — {count} wildcard files found"
    print(f"[JStudio Wildcards] {msg}")
    return web.json_response({"message": msg, "count": count, "folder": folder})


def setup_routes(app):
    app.router.add_post("/api/jstudio/reload_wildcards", reload_wildcards_handler)
