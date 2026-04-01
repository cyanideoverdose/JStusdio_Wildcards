from aiohttp import web
from .node import reload_wildcards, set_wildcards_folder, _get_wildcards_folder
import os


async def reload_wildcards_handler(request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    folder = data.get("wildcards_folder", "").strip()
    if folder:
        set_wildcards_folder(folder)

    reload_wildcards()

    count = 0
    detected_folder = _get_wildcards_folder()
    if detected_folder and os.path.isdir(detected_folder):
        for root, dirs, files in os.walk(detected_folder):
            count += sum(1 for f in files if f.endswith((".txt", ".yaml", ".yml")))

    msg = f"Wildcards reloaded. {count} files found in: {detected_folder or 'folder not found'}"
    print(f"[JStudio Wildcards] {msg}")
    return web.json_response({"message": msg, "count": count, "folder": detected_folder})


def setup_routes(app):
    app.router.add_post("/jstudio/reload_wildcards", reload_wildcards_handler)
