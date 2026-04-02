import os
import re
import random
import yaml
from datetime import datetime
from jinja2 import Environment, BaseLoader, StrictUndefined

# ─────────────────────────────────────────────
# Wildcard cache
# ─────────────────────────────────────────────
_wildcard_cache = {}
_wildcards_folder = None


def reload_wildcards():
    global _wildcard_cache
    _wildcard_cache = {}


def _find_wildcards_folder():
    """
    Walk up from this file looking for a folder that contains both
    'custom_nodes' and 'wildcards' as siblings — that's the ComfyUI root.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        if (os.path.isdir(os.path.join(here, "custom_nodes")) and
                os.path.isdir(os.path.join(here, "wildcards"))):
            found = os.path.join(here, "wildcards")
            print(f"[JStudio Wildcards] Wildcards folder: {found}")
            return found
        here = os.path.dirname(here)
    print("[JStudio Wildcards] WARNING: Could not find wildcards folder.")
    return None


def _get_wildcards_folder():
    global _wildcards_folder
    if _wildcards_folder and os.path.isdir(_wildcards_folder):
        return _wildcards_folder
    _wildcards_folder = _find_wildcards_folder()
    return _wildcards_folder


def _load_wildcard(key: str):
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
    if len(parts) > 1:
        txt_path = os.path.join(folder, *parts[:-1], parts[-1] + ".txt")
        if not os.path.isfile(txt_path):
            txt_path = os.path.join(folder, *parts) + ".txt"
    else:
        txt_path = os.path.join(folder, base + ".txt")

    if os.path.isfile(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        _wildcard_cache[key] = lines
        return lines

    print(f"[JStudio Wildcards] WARNING: No file found for key: {key}")
    return [f"__{key}__"]


def _extract_yaml_entries(data, subkey):
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
# Resolvers
# ─────────────────────────────────────────────

def _resolve_wildcard_tags(text: str, rng: random.Random, depth=0) -> str:
    if depth > 20:
        return text

    def replace(m):
        key = m.group(1)
        entries = _load_wildcard(key)
        chosen = rng.choice(entries).strip()
        if "{%" in chosen or "{{" in chosen:
            chosen = _resolve_jinja2(chosen, rng)
        return _resolve_wildcard_tags(chosen, rng, depth + 1)

    return re.sub(r'__([a-zA-Z0-9_\-/]+)__', replace, text)


def _resolve_weighted_choice(text: str, rng: random.Random) -> str:
    def replace_choice(m):
        inner = m.group(1)
        options = inner.split("|")
        weighted = []
        unweighted = []
        for opt in options:
            pm = re.match(r'^(\d+(?:\.\d+)?)%(.*)$', opt)
            if pm:
                weighted.append((float(pm.group(1)) / 100.0, pm.group(2)))
            else:
                unweighted.append(opt)
        if weighted:
            total = sum(w for w, _ in weighted)
            remaining = max(0.0, 1.0 - total)
            choices = list(weighted)
            if unweighted:
                per = remaining / len(unweighted)
                for u in unweighted:
                    choices.append((per, u))
            r = rng.random()
            cumulative = 0.0
            for prob, val in choices:
                cumulative += prob
                if r <= cumulative:
                    return val.strip()
            return choices[-1][1].strip()
        else:
            return rng.choice(unweighted).strip()

    for _ in range(10):
        new_text = re.sub(r'\{([^{}]+)\}', replace_choice, text)
        if new_text == text:
            break
        text = new_text
    return text


def _build_jinja_env(rng: random.Random) -> Environment:
    """Shared Jinja2 environment — positive and negative share variable scope."""
    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    now = datetime.now()
    m, d = now.month, now.day

    def wildcard(key):
        return rng.choice(_load_wildcard(key))

    env.globals.update({
        "wildcard": wildcard,
        "wc_all": _load_wildcard,
        "month": m, "day": d, "year": now.year, "now": now,
        "random": rng,
        "is_halloween":  (m == 10),
        "is_christmas":  (m == 12 or (m == 11 and d >= 25)),
        "is_valentines": (m == 2 and d <= 14),
        "is_holiday":    (m == 10) or (m == 12) or (m == 11 and d >= 25) or (m == 2 and d <= 14),
    })
    return env


def _resolve_jinja2(text: str, rng: random.Random, env=None) -> str:
    if "{%" not in text and "{{" not in text:
        return text
    try:
        if env is None:
            env = _build_jinja_env(rng)
        return env.from_string(text).render()
    except Exception as e:
        return f"[Jinja2 error: {e}] {text}"


def _clean(text: str) -> str:
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.strip(',').strip()


def resolve_prompt(positive: str, negative: str, seed: int) -> tuple:
    """
    Returns (resolved_positive, resolved_negative).
    Both use the same seed and share the same Jinja2 environment
    so variables set in positive are available in negative.
    """
    rng = random.Random(seed)
    env = _build_jinja_env(rng)

    def _render(t):
        if "{%" not in t and "{{" not in t:
            return t
        try:
            return env.from_string(t).render()
        except Exception as e:
            return f"[Jinja2 error: {e}] {t}"

    def _resolve(t):
        t = _render(t)
        t = _resolve_wildcard_tags(t, rng)
        t = _resolve_weighted_choice(t, rng)
        return _clean(t)

    # Positive resolves first — sets Jinja2 variables
    resolved_pos = _resolve(positive)

    # Negative resolves second — can reference variables set during positive
    resolved_neg = _resolve(negative) if negative.strip() else ""

    return resolved_pos, resolved_neg


# Pre-warm at import
_get_wildcards_folder()


# ─────────────────────────────────────────────
# ComfyUI Node
# ─────────────────────────────────────────────

class JStudioWildcards:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "__lucky_ladies/random__",
                    "dynamicPrompts": False,
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": "__negatives/global__",
                    "dynamicPrompts": False,
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("resolved_prompt", "resolved_negative",)
    FUNCTION = "process"
    CATEGORY = "Joaquin Studios"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def process(self, prompt: str, negative_prompt: str, seed: int):
        resolved_pos, resolved_neg = resolve_prompt(prompt, negative_prompt, seed)
        print(f"[JStudio Wildcards] Seed: {seed}")
        return (resolved_pos, resolved_neg,)


NODE_CLASS_MAPPINGS = {
    "JStudioWildcards": JStudioWildcards,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JStudioWildcards": "🎲 JStudio Wildcards",
}
