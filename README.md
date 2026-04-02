# JStudio Wildcards — ComfyUI Custom Node

A wildcard prompt node for ComfyUI with **Jinja2 templating**, **YAML wildcard support**, and **hot-reload** — no server restart needed when you update your wildcard files.

Built by **Joaquin Studios** (Leizer on Civitai).

---

## Features

- ✅ `__wildcard__` and `__folder/key__` syntax for `.txt` and `.yaml` files
- ✅ `{option1|option2|option3}` random choice syntax
- ✅ `{33%option_a|option_b}` weighted probability syntax
- ✅ Full **Jinja2** template support with date-aware conditional logic
- ✅ **Hot-reload** button — update wildcard files without restarting ComfyUI
- ✅ Nested YAML support with slash key navigation
- ✅ Holiday-aware wildcard pools (Halloween, Christmas, Valentine's)
- ✅ Seeded randomness — connect to your KSampler seed for reproducible results
- ✅ Automatic comma and whitespace cleanup
- ✅ Auto-detects your ComfyUI wildcards folder — no configuration needed

---

## Installation

### Via ComfyUI Manager
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

## Node

### 🎲 JStudio Wildcards

**Inputs:**

| Input | Type | Description |
|-------|------|-------------|
| `prompt` | STRING | Your prompt with wildcard tags and/or Jinja2 templates |
| `seed` | INT | Random seed — connect to KSampler seed for reproducible results |

**Output:** `resolved_prompt` (STRING) — the fully resolved prompt, ready to connect to CLIP Text Encode

**Button:** 🔄 Refresh Wildcards — reloads all wildcard files from disk instantly, no restart needed

---

## Syntax Reference

### Wildcard files (txt)
```
__scene__
__pose/action__
__lighting__
```

### YAML wildcards (nested keys)
```
__characters/hatsune_miku__
__characters/random__
__outfits/school_uniform__
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
  {{ wildcard("characters/random") }}, witch hat, dark magic
{% elif is_christmas %}
  {{ wildcard("characters/random") }}, santa outfit, snow
{% else %}
  {{ wildcard("characters/random") }}, {{ wildcard("outfits/casual") }}
{% endif %}
```

**Available Jinja2 globals:**

| Variable | Description |
|----------|-------------|
| `wildcard("key")` | Pick one random entry from a wildcard file or YAML key |
| `wc_all("key")` | Get the full list from a wildcard file |
| `month` | Current month (integer) |
| `day` | Current day (integer) |
| `year` | Current year (integer) |
| `now` | Full datetime object |
| `is_halloween` | True during October |
| `is_christmas` | True during December and late November |
| `is_valentines` | True February 1–14 |
| `is_holiday` | True if any holiday flag is active |
| `random` | Seeded Python random instance |

---

## Wildcard File Formats

### TXT — one entry per line
```
foggy city street at night
neon-lit alley
rooftop under the moon
# Lines starting with # are ignored
```

### YAML — flat list under a key
```yaml
scenes:
  - foggy city street at night
  - neon-lit alley
  - rooftop under the moon
```

### YAML — nested character sheets
```yaml
hatsune_miku:
  - "1girl, long twintails, teal hair, teal eyes, slim, white dress shirt, black skirt"

zero_two:
  - "1girl, long pink hair, red horns, green eyes, white and red uniform, tall"

rem:
  - "1girl, short blue hair, blue eyes, maid uniform, petite"

random:
  - "__characters/hatsune_miku__"
  - "__characters/zero_two__"
  - "__characters/rem__"
```

---

## Conditional Tag Example

Gate body or outfit tags based on resolved camera angle or outfit type:

```jinja2
{% set char = wildcard("characters/zero_two") %}
{% set cam = wildcard("camera_angle") %}
{% set is_rear = "behind" in cam or "back" in cam %}
{{ char }}{% if is_rear %}, large ass, bubble butt{% endif %},
{{ wildcard("outfits/casual") }}, {{ cam }}, __lighting__, __scene__
```

---

## Folder Auto-Detection

The node automatically finds your wildcards folder by walking up from its install location until it finds a directory containing both `custom_nodes` and `wildcards` as siblings — that's your ComfyUI root. No manual path configuration needed.

---

## License

MIT License — free to use, modify, and distribute.

---

*Joaquin Studios*