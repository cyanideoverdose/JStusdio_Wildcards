import os
import re
import random
import yaml
from datetime import datetime
from jinja2 import Environment, BaseLoader, StrictUndefined

# ─────────────────────────────────────────────
# Wildcard file cache — cleared on refresh
# ─────────────────────────────────────────────
_wildcard_cache = {}
_wildcards_folder = None


def set_wildcards_folder(path: str):
    global _wildcards_folder
    _wildcards_folder = path


def reload_wildcards():
    global _wildcard_cache
    _wildcard_cache = {}


def _get_wildcards_folder():
    if _wildcards_folder and os.path.isdir(_wildcards_folder):
        return _wildcards_folder
    # Auto-detect: walk up from this file to find ComfyUI root
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        candidate = os.path.join(here, "wildcards")
        if os.path.isdir(candidate):
            return candidate
        here = os.path.dirname(here)
    return None


def _load_wildcard(key: str):
    """
    Load wildcard entries for a given key.
    key examples:
      "scene"                   → wildcards/scene.txt
      "lucky_ladies/kalasir"    → wildcards/lucky_ladies.yaml  key=kalasir
      "lucky_ladies"            → wildcards/lucky_ladies.yaml  root list OR all values
    Returns a list of strings.
    """
    if key in _wildcard_cache:
        return _wildcard_cache[key]

    folder = _get_wildcards_folder()
    if not folder:
        return [f"__{key}__"]

    parts = key.split("/")
    base = parts[0]
    subkey = "/".join(parts[1:]) if len(parts) > 1 else None

    # Try YAML first
    for ext in (".yaml", ".yml"):
        yaml_path = os.path.join(folder, base + ext)
        if os.path.isfile(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            entries = _extract_yaml_entries(data, subkey)
            _wildcard_cache[key] = entries
            return entries

    # Try txt
    txt_path = os.path.join(folder, *parts[:-1], parts[-1] + ".txt") if len(parts) > 1 else os.path.join(folder, base + ".txt")
    # Also try subfolder
    if not os.path.isfile(txt_path) and len(parts) > 1:
        txt_path = os.path.join(folder, *parts) + ".txt"

    if os.path.isfile(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]
        _wildcard_cache[key] = lines
        return lines

    return [f"__{key}__"]


def _extract_yaml_entries(data, subkey: str | None):
    """
    Navigate nested YAML structure using a slash-delimited subkey.
    If subkey is None, return all leaf strings from the root.
    """
    if subkey is None:
        return _flatten_yaml(data)

    parts = subkey.split("/")
    node = data
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return [f"(missing yaml key: {subkey})"]

    return _flatten_yaml(node)


def _flatten_yaml(node):
    """Recursively collect all string leaf values from a YAML node."""
    if isinstance(node, list):
        results = []
        for item in node:
            results.extend(_flatten_yaml(item))
        return results
    elif isinstance(node, dict):
        results = []
        for v in node.values():
            results.extend(_flatten_yaml(v))
        return results
    elif isinstance(node, str):
        return [node]
    else:
        return [str(node)]


# ─────────────────────────────────────────────
# Syntax resolvers
# ─────────────────────────────────────────────

def _resolve_wildcard_tags(text: str, rng: random.Random, depth=0) -> str:
    """Resolve __wildcard__ tags recursively."""
    if depth > 20:
        return text

    def replace_wildcard(m):
        key = m.group(1)
        entries = _load_wildcard(key)
        chosen = rng.choice(entries)
        # Recurse to resolve nested wildcards
        return _resolve_wildcard_tags(chosen, rng, depth + 1)

    return re.sub(r'__([a-zA-Z0-9_\-/]+)__', replace_wildcard, text)


def _resolve_weighted_choice(text: str, rng: random.Random) -> str:
    """
    Resolve {option1|option2} and {33%option|option2} syntax.
    Weighted: {33%foo|bar} means 33% chance of foo, 67% of bar.
    Empty option: {33%foo|} means 33% foo, 67% empty string.
    """
    def replace_choice(m):
        inner = m.group(1)
        options = inner.split("|")

        weighted = []
        unweighted = []

        for opt in options:
            pct_match = re.match(r'^(\d+(?:\.\d+)?)%(.*)$', opt)
            if pct_match:
                weighted.append((float(pct_match.group(1)) / 100.0, pct_match.group(2)))
            else:
                unweighted.append(opt)

        if weighted:
            # Build probability distribution
            total_weighted = sum(w for w, _ in weighted)
            remaining = max(0.0, 1.0 - total_weighted)
            choices = [(w, v) for w, v in weighted]
            if unweighted:
                per_unweighted = remaining / len(unweighted)
                for u in unweighted:
                    choices.append((per_unweighted, u))
            r = rng.random()
            cumulative = 0.0
            for prob, val in choices:
                cumulative += prob
                if r <= cumulative:
                    return val.strip()
            return choices[-1][1].strip()
        else:
            return rng.choice(unweighted).strip()

    # Iteratively resolve until no more {|} patterns (handles nesting)
    for _ in range(10):
        new_text = re.sub(r'\{([^{}]+)\}', replace_choice, text)
        if new_text == text:
            break
        text = new_text
    return text


# ─────────────────────────────────────────────
# Jinja2 environment with wildcard support
# ─────────────────────────────────────────────

def _build_jinja_env(rng: random.Random) -> Environment:
    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)

    # Expose wildcard function inside Jinja2
    def wildcard(key):
        entries = _load_wildcard(key)
        return rng.choice(entries)

    def wc_all(key):
        return _load_wildcard(key)

    def get_month():
        return datetime.now().month

    def get_day():
        return datetime.now().day

    def get_year():
        return datetime.now().year

    env.globals["wildcard"] = wildcard
    env.globals["wc_all"] = wc_all
    env.globals["month"] = get_month()
    env.globals["day"] = get_day()
    env.globals["year"] = get_year()
    env.globals["now"] = datetime.now()
    env.globals["random"] = rng

    # Holiday helpers
    m = get_month()
    d = get_day()
    env.globals["is_halloween"] = (m == 10)
    env.globals["is_christmas"] = (m == 12 or (m == 11 and d >= 25))
    env.globals["is_valentines"] = (m == 2 and d <= 14)
    env.globals["is_holiday"] = env.globals["is_halloween"] or env.globals["is_christmas"] or env.globals["is_valentines"]

    return env


def _resolve_jinja2(text: str, rng: random.Random) -> str:
    """Render text as a Jinja2 template if it contains Jinja2 syntax."""
    if "{%" not in text and "{{" not in text:
        return text
    try:
        env = _build_jinja_env(rng)
        template = env.from_string(text)
        return template.render()
    except Exception as e:
        return f"[Jinja2 error: {e}] {text}"


# ─────────────────────────────────────────────
# Main resolver — full pipeline
# ─────────────────────────────────────────────

# Thread-local storage for character tracking
_last_character = {"name": "unknown"}


def resolve_prompt(text: str, seed: int, character_wildcard: str = "") -> tuple:
    """
    Returns (resolved_prompt, character_name).
    character_wildcard: the wildcard key to watch for character selection
    e.g. "lucky_ladies" will track which character was picked from that file.
    """
    rng = random.Random(seed)
    character_name = "unknown"

    # ── Track character selection ──────────────────────────────────────
    # If a character_wildcard is specified, intercept the first resolution
    # of that key and capture the chosen entry's key name.
    if character_wildcard.strip():
        watch_key = character_wildcard.strip().strip("_")

        original_load = _load_wildcard

        def tracking_load(key):
            nonlocal character_name
            result = original_load(key)
            # If this is a resolution of the watched wildcard's random/subkey
            # try to figure out which character was picked
            if key.startswith(watch_key + "/") or key == watch_key:
                subkey = key.split("/")[-1] if "/" in key else key
                if subkey not in ("random", watch_key):
                    character_name = subkey
            return result

        # Patch temporarily — resolve with tracking
        import builtins
        _patch_load(tracking_load)

    # 1. Jinja2 first
    text = _resolve_jinja2(text, rng)

    # 2. Resolve __wildcard__ tags — with character tracking via regex intercept
    if character_wildcard.strip():
        watch_key = character_wildcard.strip().strip("_")
        def replace_wildcard_tracked(m):
            nonlocal character_name
            key = m.group(1)
            entries = _load_wildcard(key)
            chosen = rng.choice(entries)
            # Detect character selection: key is watch_key/something specific
            parts = key.split("/")
            if parts[0] == watch_key and len(parts) > 1 and parts[-1] != "random":
                character_name = parts[-1]
            # Also detect when the chosen entry is itself a wildcard reference
            char_match = re.match(r'^__' + re.escape(watch_key) + r'/([^_]+)__$', chosen.strip())
            if char_match:
                candidate = char_match.group(1)
                if candidate != "random":
                    character_name = candidate
            resolved = _resolve_wildcard_tags(chosen, rng, depth=1)
            return resolved

        text = re.sub(r'__([a-zA-Z0-9_\-/]+)__', replace_wildcard_tracked, text)
    else:
        text = _resolve_wildcard_tags(text, rng)

    # 3. Resolve {option|option} syntax
    text = _resolve_weighted_choice(text, rng)

    # 4. Clean up extra commas/spaces
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.strip(',').strip()

    # Sanitize character name for use in filenames
    char_safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', character_name).strip('_') or "unknown"

    return text, char_safe


def _patch_load(fn):
    """No-op — tracking is done inline above."""
    pass


# ─────────────────────────────────────────────
# ComfyUI Node
# ─────────────────────────────────────────────

class JStudioWildcards:
    WILDCARDS_FOLDER = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "__lucky_ladies/random__",
                    "dynamicPrompts": False,
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                }),
                "wildcards_folder": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
                "character_wildcard": ("STRING", {
                    "default": "lucky_ladies",
                    "multiline": False,
                    "tooltip": "Name of your character wildcard file (without extension). Used to extract the character name for filenames. e.g. 'lucky_ladies'"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("resolved_prompt", "character_name",)
    FUNCTION = "process"
    CATEGORY = "Joaquin Studios"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def process(self, prompt: str, seed: int, wildcards_folder: str, character_wildcard: str = "lucky_ladies"):
        if wildcards_folder.strip():
            set_wildcards_folder(wildcards_folder.strip())

        resolved, char_name = resolve_prompt(prompt, seed, character_wildcard)
        print(f"[JStudio Wildcards] Character: {char_name}")
        return (resolved, char_name,)


class JStudioWildcardsReload:
    """Utility node — click to reload all wildcard files from disk."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "wildcards_folder": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "reload"
    CATEGORY = "Joaquin Studios"
    OUTPUT_NODE = True

    def reload(self, wildcards_folder: str):
        if wildcards_folder.strip():
            set_wildcards_folder(wildcards_folder.strip())
        reload_wildcards()
        count = 0
        folder = _get_wildcards_folder()
        if folder:
            for root, dirs, files in os.walk(folder):
                count += sum(1 for f in files if f.endswith((".txt", ".yaml", ".yml")))
        msg = f"Wildcards reloaded. Found {count} files in {folder or 'auto-detected folder'}."
        print(f"[JStudio Wildcards] {msg}")
        return (msg,)


NODE_CLASS_MAPPINGS = {
    "JStudioWildcards": JStudioWildcards,
    "JStudioWildcardsReload": JStudioWildcardsReload,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JStudioWildcards": "🎲 JStudio Wildcards",
    "JStudioWildcardsReload": "🔄 JStudio Reload Wildcards",
}
