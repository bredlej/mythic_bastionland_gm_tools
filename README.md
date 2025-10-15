# `roll` — tiny tabletop RNG & oracle CLI (made for Mythic Bastionland)

### DISCLAIMER: This tool was vibe coded with ChatGPT 5

A single-file Python tool for GMs/players:

* 🎲 **Dice expressions**: `2d6 + d4 - 1`, `d20`, `100`
* 🔮 **Yes/No Oracle**: `-o`, `-ol` (likely), `-ou` (unlikely)
* ✨ **Spark tables** from CSV/JSON: `-s LAND`, `-s SKY`
* 🌲 **Wilderness roll**: `-w`
* 🍀 **Luck roll**: `-l`
* ⚖️ **Unresolved situations**: `-u`
* 🏘️ **Local mood**: `-m`

Works great for hex-crawls, solo play, and fast scene prompts.

---

## Contents

* [Requirements](#requirements)
* [Installation](#installation)
* [Quick start](#quick-start)
* [Usage](#usage)
* [Spark tables](#spark-tables)

  * [CSV format (Numbers export)](#csv-format-numbers-export)
  * [JSON format](#json-format)
  * [Pointing to your data](#pointing-to-your-data)
* [Examples](#examples)
* [Troubleshooting](#troubleshooting)
* [License](#license)

---

## Requirements

* Python **3.8+** (works on macOS/Linux/Windows)
* Optional: your own Spark tables file (CSV or JSON)

---

## Installation

### macOS / Linux

1. Put the script in your project as `roll.py` and make it executable:

```bash
chmod +x roll.py
```

2. (Optional) Install it onto your PATH so you can just type `roll`:

```bash
mv roll.py ~/.local/bin/roll
# ensure ~/.local/bin is on PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc   # or ~/.zshrc
source ~/.bashrc                                          # or ~/.zshrc
```

Now you can run:

```bash
roll d20 + d12
```

### Windows

* Use the Python launcher:

```powershell
py roll.py d20 + d12
```

Or create a small `roll.cmd` next to the script:

```cmd
@echo off
py "%~dp0roll.py" %*
```

Add that folder to your PATH to run `roll` from anywhere.

---

## Quick start

```bash
# Dice
roll 2d6 + d4 - 1

# Oracle
roll -o
roll -ol
roll -ou

# Spark tables (CSV/JSON)
roll --list-spark --spark-file "sparks_en.csv"
roll -s LAND # pick one from the $SPARK_FILE file
roll -s LAND --spark-file "sparks_en.csv" # pick one from each LAND column via 2d12
roll -s NATURE --spark-file "sparks_en.csv" # pick a random table within sheet NATURA

# Narrative helpers
roll -w        # Wilderness roll
roll -l        # Luck roll
roll -u        # Unresolved situation
roll -m        # Local mood
```

---

## Usage

```text
roll [-o | -ol | -ou] [-w] [-l] [-u] [-m]
     [-s SHEET|TABLE] [--spark-file FILE] [--list-spark]
     [EXPRESSION]

Flags:
  -o            Standard oracle (d6: 1–3 YES, 4–5 NO, 6 TWIST)
  -ol           Likely oracle     (d6: 1–4 YES, 5 NO, 6 TWIST)
  -ou           Unlikely oracle   (d6: 1–2 YES, 3–5 NO, 6 TWIST)

  -w            Wilderness roll   (d6: 1 random Myth omen; 2–3 nearest Myth omen; 4–6 Hex Landmark/clear)
  -l            Luck roll         (d6: 1 Crisis; 2–3 Problem; 4–6 Blessing)
  -u            Unresolved roll   (d6: 1 as bad as possible; else unpredictable)
  -m            Local mood        (d6: 1 looming woe; 2–3 decline; 4–6 all seems well)

Spark tables:
  -s NAME       If NAME is a TABLE → roll it (2d12: one pick per column).
                If NAME is a SHEET → randomly choose a table in that sheet, then roll it.
  --spark-file  Path to CSV/JSON (default: "Spark Tables PL.csv" or env $SPARK_FILE)
  --list-spark  Print available sheets & tables (from --spark-file)

Expression:
  Dice like "2d6 + d4 - 1", "d20", or "100" (equiv. to d100).
```

You can combine features; outputs print in order. For example:

```bash
roll -ol -s LAND d20 + d12 --spark-file "sparks_en.csv"
```

---

## Spark tables

The script supports **two formats**:

### CSV format (Numbers export)

If you export a Numbers document with multiple sheets/tables, you may get a CSV where **everything is in one column**, using semicolons between fields. The parser expects sections like:

```
NATURE:
;LAND;
;Trait;Landscape
1;Barren;Swamp
2;Dry;Heath
3;Gray;Cliffs
4;Sparse;Peaks
5;Sharp;Forest
6;Vibrant;Valley
7;Calm;Hills
8;Soft;Meadow
9;Overgrown;Marsh
10;Bright;Lakes
11;Soaked;Glades
12;Lush;Plain
```

Rules:

* A **sheet header** is a line with `SHEET:` and **no semicolons**.
* A **table start** looks like `;TABLE;`.
* The next line is the **header**: `;Column1;Column2`.
* Then 12+ lines of `index;Value1;Value2`.

Names are matched **case/space/diacritic-insensitively**; e.g. `LAND`, `land`, `Land` all match.

### JSON format

You can also provide a JSON file with this exact shape:

```json
{
  "NATURE": {
    "LAND": {
      "columns": ["Trait", "Landscape"],
      "rows": [
        ["Barren", "Swamp"],
        ["Dry", "Heath"]
        // ... 12+ rows
      ]
    }
  }
}
```

### Pointing to your data

* Use `--spark-file path/to/file.csv` (or `.json`)
* Or set an environment variable so you don’t have to pass the flag:

```bash
export SPARK_FILE="/absolute/path/to/sparks_en.csv"
```

List what's available:

```bash
roll --list-spark --spark-file "$SPARK_FILE"
```

---

## Examples

```bash
# Basic dice
roll d20
roll 2d6 + d4 - 1

# Oracle
roll -o
roll -ol
roll -ou

# Spark: direct table
roll -s LAND --spark-file "sparks_en.csv"
# → 🗺️  Spark → Sheet: NATURE | Table: LAND
#   ✨ Spark 2d12 → [12, 1]
#   Cecha: 'Lush' + Krajobraz: 'Swamp'

# Spark: random table within sheet
roll -s NATURE --spark-file "sparks_en.csv"

# Narrative helpers
roll -w
roll -l
roll -u
roll -m

# Combine
roll -m -w -l -s LAND d20 + d12 --spark-file "sparks_en.csv"
```

---

## Troubleshooting

* **`command not found: roll`**
  Ensure the script is on your PATH and executable:

  ```bash
  chmod +x roll.py && mv roll.py ~/.local/bin/roll
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
  ```

* **Spark file not found**
  Pass `--spark-file` or set `SPARK_FILE`:

  ```bash
  roll --list-spark --spark-file "sparks_en.csv"
  ```

* **CSV parsing issues**
  The CSV must follow the Numbers-export single-column/semicolon pattern (see above). If it’s messy, convert it to the JSON shape shown and use that instead.

* **Unicode table names (e.g., `LĄD`) not matching**
  The script normalizes diacritics and spaces. Try `roll -s LAD` or `roll -s "LĄD"`.

---

## License

MIT — do whatever you like, attribution appreciated.
If you publish tweaks, PRs welcome!

---

Happy rolling! 🎲✨
