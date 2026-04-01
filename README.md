# JStudio Wildcards — ComfyUI Custom Node

A wildcard prompt node for ComfyUI with **Jinja2 templating**, **YAML wildcard support**, and **hot-reload** — no server restart needed when you update your wildcard files.

Built by **Joaquin Studios** (CyanideOverdose on Civitai).

---

## Features

- ✅ `__wildcard__` and `__folder/key__` syntax for `.txt` and `.yaml` files
- ✅ `{option1|option2|option3}` random choice syntax
- ✅ `{33%option_a|option_b}` weighted probability syntax
- ✅ Full **Jinja2** template support with date-aware logic
- ✅ **Hot-reload** button — update wildcard files without restarting ComfyUI
- ✅ Nested YAML support with key navigation
- ✅ Holiday-aware wildcard pools (Halloween, Christmas, Valentine's)
- ✅ Seeded randomness — connect to your KSampler seed for reproducible results
- ✅ Automatic comma and whitespace cleanup

---

## Installation

### Via ComfyUI Manager (recommended)
1. Open ComfyUI Manager
2. Click **Install via Git URL**
3. Paste: `https://github.com/cyanideoverdose/jstudio-wildcards`
4. Restart ComfyUI once

### Manual
1. Clone or download this repo into `ComfyUI/custom_nodes/jstudio_wildcards/`
2. Install dependencies:
   ```bash
   pip install jinja2 pyyaml
   ```
3. Restart ComfyUI once

---

## Nodes

### 🎲 JStudio Wildcards
The main prompt resolver. Connects to your CLIP Text Encode node.

**Inputs:**
| Input | Type | Description |
|-------|------|-------------|
| `prompt` | STRING | Your prompt with wildcard tags and/or Jinja2 templates |
| `seed` | INT | Random seed — connect to KSampler seed for sync |
| `wildcards_folder` | STRING | Path to wildcards folder (leave blank to auto-detect) |

**Output:** `resolved_prompt` (STRING) — the fully resolved prompt string

**Button:** 🔄 Refresh Wildcards — reloads all files from disk instantly, no restart needed

---

### 🔄 JStudio Reload Wildcards
Standalone reload utility node. Useful if you want reload control separate from the main node.

---

## Syntax Reference

### Wildcard files (txt)
```
__scene__
__pose-club/club_area__
```

### YAML wildcards (nested keys)
```
__characters/kalasir__
__characters/random__
__outfits/lucky_lady__
```

### Random choice
```
{option1|option2|option3}
```

### Weighted choice
```
{33%option_a|option_b}          → 33% a, 67% b
{25%foo|25%bar|baz}             → 25% foo, 25% bar, 50% baz
{33%outerwear|}                 → 33% outerwear, 67% empty string
```

### Jinja2 templates
```jinja2
{% if is_halloween %}
  {{ wildcard("characters/random") }}, {{ wildcard("outfits/halloween") }}
{% elif is_christmas %}
  {{ wildcard("characters/random") }}, {{ wildcard("outfits/christmas") }}
{% else %}
  {{ wildcard("characters/random") }}, {{ wildcard("outfits/casual") }}
{% endif %}
```

**Available Jinja2 globals:**

| Variable | Description |
|----------|-------------|
| `wildcard("key")` | Pick one random entry from a wildcard file |
| `wc_all("key")` | Get full list from a wildcard file |
| `month` | Current month (integer) |
| `day` | Current day (integer) |
| `year` | Current year (integer) |
| `now` | Full datetime object |
| `is_halloween` | True during October |
| `is_christmas` | True during December and late November |
| `is_valentines` | True February 1–14 |
| `is_holiday` | True if any holiday is active |
| `random` | Seeded Python random instance |

### Conditional body tags example
```jinja2
{% set cam = wildcard("camera_angle") %}
{{ cam }},
{% if "behind" in cam or "back" in cam %}
  large ass, bubble butt,
{% endif %}
{{ wildcard("characters/random") }}
```

---

## Wildcard File Formats

### TXT — one entry per line
```
foggy twilight city street
neon-lit alley
rooftop under the moon
# This is a comment and will be ignored
```

### YAML — flat list
```yaml
scenes:
  - foggy twilight city street
  - neon-lit alley
  - rooftop under the moon
```

### YAML — nested keys
```yaml
characters:
  kalasir:
    - "pale porcelain skin, long wavy black hair, blue eyes..."
  amelie:
    - "cobalt blue skin, long red hair, gold eyes..."
  random:
    - "__characters/kalasir__"
    - "__characters/amelie__"
```

---

## Wildcard Folder Auto-Detection

The node walks up from its install location looking for a `wildcards` folder automatically.

If your wildcards are in a custom location, set the `wildcards_folder` input explicitly:
```
C:/ComfyUI/wildcards
/home/user/ComfyUI/wildcards
```

---

## License

MIT License — free to use, modify, and distribute.

---

*Joaquin Studios — built for the Twilight Dust production pipeline*
