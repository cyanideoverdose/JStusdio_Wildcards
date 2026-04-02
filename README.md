# JStudio Wildcards — ComfyUI Custom Node

A wildcard prompt node for ComfyUI with **Jinja2 templating**, **YAML wildcard support**, **negative prompt resolution**, and **hot-reload** — no server restart needed when you update your wildcard files.

Built by **Joaquin Studios** (Leizer on Civitai).

---

## Features

- ✅ `__wildcard__` and `__folder/key__` syntax for `.txt` and `.yaml` files
- ✅ `{option1|option2|option3}` random choice syntax
- ✅ `{33%option_a|option_b}` weighted probability syntax
- ✅ Full **Jinja2** template support with date-aware logic
- ✅ **Negative prompt** input with full wildcard and Jinja2 support
- ✅ **Shared Jinja2 scope** — variables set in positive prompt are available in negative
- ✅ **Inline separator** — write positive and negative in one template with `###NEGATIVE###`
- ✅ **Hot-reload** button — update wildcard files without restarting ComfyUI
- ✅ Nested YAML support with key navigation
- ✅ Holiday-aware wildcard pools (Halloween, Christmas, Valentine's)
- ✅ Seeded randomness — connect to your KSampler seed for reproducible results
- ✅ Automatic comma and whitespace cleanup
- ✅ `character_name` output for automatic filename tagging

---

## Installation

### Via ComfyUI Manager (recommended)
1. Open ComfyUI Manager
2. Click **Install via Git URL**
3. Paste: `https://github.com/cyanideoverdose/JStudio_Wildcards`
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
The main prompt resolver.

**Inputs:**
| Input | Type | Description |
|-------|------|-------------|
| `prompt` | STRING | Positive prompt with wildcard tags and/or Jinja2 templates |
| `seed` | INT | Random seed — connect to KSampler seed for sync |
| `wildcards_folder` | STRING | Path to wildcards folder (leave blank to auto-detect) |
| `character_wildcard` | STRING | Wildcard file to watch for character name extraction |
| `negative_prompt` | STRING (optional) | Negative prompt — supports wildcards and Jinja2, shares variable scope with positive |

**Outputs:**
| Output | Type | Description |
|--------|------|-------------|
| `resolved_prompt` | STRING | Fully resolved positive prompt |
| `resolved_negative` | STRING | Fully resolved negative prompt |
| `character_name` | STRING | Detected character name for use in filenames |

**Button:** 🔄 Refresh Wildcards — reloads all files from disk instantly, no restart needed

---

### 🔄 JStudio Reload Wildcards
Standalone reload utility node. Useful if you want reload control as a separate node in your workflow.

---

## Syntax Reference

### Wildcard files (txt)
```
__scene__
__pose/camera_angle__
__outfits/standard__
```

### YAML wildcards (nested keys)
```
__characters/my_cast/char_a__
__prompts/my_prompts/standard__
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

---

## Jinja2 Templates

### Basic usage
```jinja2
{% set char_name = 'char_a' %}
{% set desc = wildcard("characters/my_cast/" ~ char_name) %}
{% set cam = wildcard("pose/camera_angle") %}
{% set is_rear = "behind" in cam or "back" in cam %}
{% if is_rear %}
  {{ wildcard("characters/my_cast/" ~ char_name ~ "_rear") }}, from_behind, back_view
{% else %}
  {{ desc }}
{% endif %}, __outfits/standard__, {{ cam }}, __skin__
```

### Inline negative with `###NEGATIVE###` separator
Write positive and negative in one template. Variables are shared across both sides:

```jinja2
{% set outfit_key = ["outfits/revealing", "outfits/standard", "outfits/bodysuit"] | random %}
{% set outfit = wildcard(outfit_key) %}
{% set is_revealing = outfit_key in ["outfits/revealing"] %}
{% set cam = wildcard("pose/camera_angle") %}
{% set is_rear = "behind" in cam %}

{{ wildcard("characters/my_cast/char_a") }}, {{ outfit }}, __pose/action__, __scene__, {{ cam }}, __skin__

###NEGATIVE###

{% if not is_revealing %}visible_nipples, exposed_breasts,{% endif %}
{% if is_rear %}looking_at_viewer, facing_camera,{% endif %}
__negatives/global__
```

### Separate negative prompt input
The `negative_prompt` input shares the same Jinja2 variable scope as the positive prompt. Variables set in the positive are available in the negative:

**Positive prompt:**
```jinja2
{% set char_name = 'char_a' %}
{% set is_clothed = true %}
{{ wildcard("characters/my_cast/" ~ char_name) }}, __outfits/standard__
```

**Negative prompt input:**
```jinja2
{% if is_clothed %}visible_nipples, exposed_breasts,{% endif %}
__negatives/global__
```

### Holiday-aware pools
```jinja2
{% if is_halloween %}
  {{ wildcard("characters/my_cast/char_a") }}, __outfits/halloween__, __scene/spooky__
{% elif is_christmas %}
  {{ wildcard("characters/my_cast/char_a") }}, __outfits/christmas__, __scene/winter__
{% else %}
  {{ wildcard("characters/my_cast/char_a") }}, __outfits/standard__, __scene/location__
{% endif %}
```

---

## Available Jinja2 Globals

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

---

## Recommended Folder Structure

```
wildcards/
  characters/
    my_cast.yaml          ← character descriptions (front + rear)
  prompts/
    my_prompts.yaml       ← reusable prompt templates
  negatives/
    global.txt            ← negatives applied to everything
    character/
      char_a.txt          ← character-specific negatives
  my_cast.yaml            ← character resolution and random list
  outfits/
  pose/
  scene/
  lighting/
  skin.txt
```

### characters/my_cast.yaml structure
```yaml
char_a: "1woman, blue skin, colored_skin, long red hair, ..."
char_a_rear: "1woman, blue skin, colored_skin, long red hair, ..."  # face/eye tags removed
char_b: "..."
char_b_rear: "..."
```

### prompts/my_prompts.yaml structure
```yaml
standard: |
  {% set desc = wildcard("characters/my_cast/" ~ char_name) %}
  {% set cam = wildcard("pose/camera_angle") %}
  {% set is_rear = "behind" in cam or "back" in cam %}
  {% if is_rear %}{{ wildcard("characters/my_cast/" ~ char_name ~ "_rear") }}, from_behind{% else %}{{ desc }}{% endif %}, __outfits/standard__, {{ cam }}, __skin__

club: |
  {% set desc = wildcard("characters/my_cast/" ~ char_name) %}
  {{ desc }}, __outfits/standard__, __scene/club__, __lighting/mood__, __pose/action__, __skin__
```

### my_cast.yaml structure
```yaml
random:
  - "__my_cast/char_a__"
  - "__my_cast/char_b__"

char_a:
  - "{% set char_name = 'char_a' %}{{ wildcard('prompts/my_prompts/standard') }}"
  - "{% set char_name = 'char_a' %}{{ wildcard('prompts/my_prompts/club') }}"

char_b:
  - "{% set char_name = 'char_b' %}{{ wildcard('prompts/my_prompts/standard') }}"
  - "{% set char_name = 'char_b' %}{{ wildcard('prompts/my_prompts/club') }}"
```

Adding a new prompt variant: edit one entry in `prompts/my_prompts.yaml`, add one line per character in `my_cast.yaml`. Adding a new character: add descriptions to `characters/my_cast.yaml`, add entries to `my_cast.yaml`.

---

## Example Wildcard Pack

A complete example wildcard pack with placeholder characters and folder structure is available in the `examples/` folder. Drop it into your wildcards directory to get a working pipeline immediately.

---

## Wildcard Folder Auto-Detection

The node walks up from its install location looking for a `wildcards` folder automatically. To use a custom location, set the `wildcards_folder` input:
```
C:/ComfyUI/wildcards
/home/user/ComfyUI/wildcards
```

---

## License

MIT License — free to use, modify, and distribute.

---

*Joaquin Studios*
