#!/usr/bin/env python3
import argparse
import json
import os
import random
import re
import sys
import unicodedata

# ---------------- Dice ----------------

DICE_TOKEN = re.compile(r'[+-]?\d*d?\d+')

def roll_expression(expr: str) -> int:
    expr = expr.lower().replace(" ", "")
    tokens = DICE_TOKEN.findall(expr)
    if not tokens:
        raise ValueError("Invalid expression. Example: 2d6 + d4 + 3")

    total = 0
    details = []

    for token in tokens:
        sign = 1
        if token.startswith('-'):
            sign = -1
            token = token[1:]
        elif token.startswith('+'):
            token = token[1:]

        m = re.fullmatch(r'(\d*)d(\d+)', token)
        if m:
            num = int(m.group(1)) if m.group(1) else 1
            sides = int(m.group(2))
            if sides <= 0 or num <= 0:
                raise ValueError("Dice and quantity must be positive.")
            rolls = [random.randint(1, sides) for _ in range(num)]
            subtotal = sum(rolls) * sign
            details.append(f"{'+' if sign > 0 else '-'}{num}d{sides}={rolls}")
            total += subtotal
        elif token.isdigit():
            val = int(token) * sign
            details.append(f"{'+' if sign > 0 else '-'}{abs(val)}")
            total += val
        else:
            raise ValueError(f"Invalid token: {token}")

    if details:
        print(" | ".join(details))
    print(f"🎲 Total: {total}")
    return total

# ---------------- New Scaled Oracle (d100) ----------------
# mode -> (left, center, right)
ORACLE_THRESHOLDS = {
    "oc":  (18, 90, 99),  # certain
    "onc": (17, 85, 98),  # nearly certain
    "ovl": (15, 75, 96),  # very likely
    "ol":  (13, 65, 94),  # likely
    "o":   (10, 50, 91),  # 50/50
    "ou":  (7, 35, 88),   # unlikely
    "ovu": (5, 25, 86),   # very unlikely
    "oni": (3, 15, 84),   # nearly impossible
    "oi":  (2, 10, 83),   # impossible
}

def is_doubles(n: int) -> bool:
    # True for 11,22,...,99 (not 100)
    return 10 <= n <= 99 and n % 11 == 0

def oracle_scaled(mode_key: str):
    if mode_key not in ORACLE_THRESHOLDS:
        raise ValueError(f"Unknown oracle mode '{mode_key}'")
    left, center, right = ORACLE_THRESHOLDS[mode_key]
    r = random.randint(1, 100)

    # Determine result
    exceptional = None
    if r < center:
        result = "YES"
        if r <= left:
            exceptional = "Exceptional YES"
    else:
        result = "NO"
        if r >= right:
            exceptional = "Exceptional NO"

    rand_event = is_doubles(r)
    # Label for printing
    mode_label = {
        "oc": "certain", "onc": "nearly certain", "ovl": "very likely",
        "ol": "likely", "o": "50/50", "ou": "unlikely",
        "ovu": "very unlikely", "oni": "nearly impossible", "oi": "impossible"
    }[mode_key]

    parts = [f"🔮 Oracle ({mode_label}) d100 → {r}  [L:{left} C:{center} R:{right}] → {result}"]
    if exceptional:
        parts.append(f"({exceptional})")
    if rand_event:
        parts.append("⚡ Random Event")
    print(" ".join(parts))

    return {
        "roll": r,
        "result": result,
        "exceptional": exceptional,
        "random_event": rand_event,
        "thresholds": (left, center, right),
        "mode": mode_label,
    }

# ---------------- Spark Tables ----------------

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", "", s).lower()

def load_spark(filepath: str):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Spark data file not found: {filepath}")

    if filepath.lower().endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    sheets = {}
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.rstrip("\n") for line in f]

    current_sheet = None
    i = 0
    while i < len(lines):
        raw = lines[i].strip()

        if ":" in raw and ";" not in raw:
            current_sheet = raw.split(":")[0].strip()
            sheets.setdefault(current_sheet, {})
            i += 1
            continue

        if raw.count(";") >= 2:
            parts = [p.strip() for p in raw.split(";")]
            if len(parts) >= 3 and parts[0] == "" and parts[1] and parts[2] == "":
                table_name = parts[1]

                col1, col2 = "Col1", "Col2"
                if i + 1 < len(lines):
                    hdr = [p.strip() for p in lines[i+1].split(";")]
                    if len(hdr) >= 3:
                        col1, col2 = hdr[1], hdr[2]

                rows = []
                j = i + 2
                while j < len(lines):
                    row = [p.strip() for p in lines[j].split(";")]
                    if len(row) >= 3 and row[0].isdigit():
                        rows.append((row[1], row[2]))
                        j += 1
                    else:
                        break

                if current_sheet is None:
                    current_sheet = "UNKNOWN"
                    sheets.setdefault(current_sheet, {})

                sheets[current_sheet][table_name] = {
                    "columns": (col1, col2),
                    "rows": rows
                }
                i = j
                continue

        i += 1

    return sheets

def list_spark(sheets_dict):
    lines = []
    for sheet, tables in sheets_dict.items():
        lines.append(f"- {sheet}: " + ", ".join(sorted(tables.keys())))
    return "\n".join(lines)

def select_table(spark_data, name: str):
    key = _norm(name)
    for sheet, tables in spark_data.items():
        if _norm(sheet) == key:
            table_name = random.choice(list(tables.keys()))
            return sheet, table_name, tables[table_name]
    for sheet, tables in spark_data.items():
        for table_name, table in tables.items():
            if _norm(table_name) == key:
                return sheet, table_name, table
    for sheet, tables in spark_data.items():
        if key in _norm(sheet):
            table_name = random.choice(list(tables.keys()))
            return sheet, table_name, tables[table_name]
        for table_name, table in tables.items():
            if key in _norm(table_name):
                return sheet, table_name, table
    raise ValueError(f"No sheet or table matched: '{name}'")

def roll_spark(table_obj):
    col1, col2 = table_obj["columns"]
    rows = table_obj["rows"]
    if len(rows) < 12:
        raise ValueError("Spark table requires at least 12 rows.")

    r1 = random.randint(1, 12)
    r2 = random.randint(1, 12)
    pick1 = rows[r1 - 1][0]
    pick2 = rows[r2 - 1][1]

    print(f"✨ Spark 2d12 → [{r1}, {r2}]")
    print(f"{col1}: '{pick1}' + {col2}: '{pick2}'")
    return [r1, r2], (pick1, pick2)

# ---------------- Narrative Rolls ----------------

def wilderness_roll():
    r = random.randint(1, 6)
    if r == 1:
        text = "Encounter the next Omen from a random Myth."
    elif r <= 3:
        text = "Encounter the next Omen from the nearest Myth."
    else:
        text = "Encounter the Hex's Landmark. Otherwise all clear."
    print(f"🌲 Wilderness d6 → {r}: {text}")
    return r, text

def luck_roll():
    r = random.randint(1, 6)
    if r == 1:
        text = "Crisis: Something immediately bad."
    elif r <= 3:
        text = "Problem: Something potentially bad."
    else:
        text = "Blessing: A welcome result."
    print(f"🍀 Luck d6 → {r}: {text}")
    return r, text

def unresolved_roll():
    r = random.randint(1, 6)
    if r == 1:
        text = "It goes as bad as it could possibly go."
    else:
        text = "It unfolds in an unpredictable way."
    print(f"⚖️  Unresolved d6 → {r}: {text}")
    return r, text

def local_mood_roll():
    r = random.randint(1, 6)
    if r == 1:
        text = "Occupied by a looming or recent woe."
    elif r <= 3:
        text = "There is a sense of things in decline."
    else:
        text = "A fine mood and all seems well enough."
    print(f"🏘️  Local Mood d6 → {r}: {text}")
    return r, text

# ---------------- CLI ----------------

def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="roll",
        description="Dice, scaled oracle (d100), Spark tables, and narrative rolls."
    )

    # New scaled oracle (mutually exclusive)
    g = p.add_mutually_exclusive_group()
    g.add_argument("-oc",  action="store_true", help="Oracle: certain (18/90/99)")
    g.add_argument("-onc", action="store_true", help="Oracle: nearly certain (17/85/98)")
    g.add_argument("-ovl", action="store_true", help="Oracle: very likely (15/75/96)")
    g.add_argument("-ol",  action="store_true", help="Oracle: likely (13/65/94)")
    g.add_argument("-o",   action="store_true", help="Oracle: 50/50 (10/50/91)")
    g.add_argument("-ou",  action="store_true", help="Oracle: unlikely (7/35/88)")
    g.add_argument("-ovu", action="store_true", help="Oracle: very unlikely (5/25/86)")
    g.add_argument("-oni", action="store_true", help="Oracle: nearly impossible (3/15/84)")
    g.add_argument("-oi",  action="store_true", help="Oracle: impossible (2/10/83)")

    # Spark options
    p.add_argument("-s", "--spark", metavar="SHEET|TABLE",
                   help="Roll a Spark table: pass a TABLE to roll it, or a SHEET to pick a random table within it.")
    p.add_argument("--spark-file", default=os.environ.get("SPARK_FILE", "Spark Tables PL.csv"),
                   help="Path to Spark data (CSV/JSON). Defaults to 'Spark Tables PL.csv' or $SPARK_FILE.")
    p.add_argument("--list-spark", action="store_true", help="List available Spark sheets and tables.")

    # Narrative rolls
    p.add_argument("-w", "--wilderness", action="store_true", help="Wilderness roll.")
    p.add_argument("-l", "--luck", action="store_true", help="Luck roll.")
    p.add_argument("-u", "--unresolved", action="store_true", help="Unresolved situation roll.")
    p.add_argument("-m", "--mood", action="store_true", help="Local Mood roll.")

    # Dice expression
    p.add_argument("expression", nargs=argparse.REMAINDER,
                   help="Dice expression, e.g. d20 + d12 or 2d6 + d4 + 3")

    return p.parse_args(argv)

def main():
    args = parse_args(sys.argv[1:])

    # Oracle selection
    mode_key = None
    if args.oc:   mode_key = "oc"
    elif args.onc: mode_key = "onc"
    elif args.ovl: mode_key = "ovl"
    elif args.ol:  mode_key = "ol"
    elif args.o:   mode_key = "o"
    elif args.ou:  mode_key = "ou"
    elif args.ovu: mode_key = "ovu"
    elif args.oni: mode_key = "oni"
    elif args.oi:  mode_key = "oi"

    if mode_key:
        oracle_scaled(mode_key)

    # Spark listing
    if args.list_spark:
        try:
            data = load_spark(args.spark_file)
            print("📚 Spark sheets & tables:")
            print(list_spark(data))
        except Exception as e:
            print(f"Error loading spark file: {e}")

    # Spark roll
    if args.spark:
        try:
            data = load_spark(args.spark_file)
            sheet, table_name, table_obj = select_table(data, args.spark)
            print(f"🗺️  Spark → Sheet: {sheet} | Table: {table_name}")
            roll_spark(table_obj)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Narrative rolls
    if args.wilderness:
        wilderness_roll()
    if args.luck:
        luck_roll()
    if args.unresolved:
        unresolved_roll()
    if args.mood:
        local_mood_roll()

    # Dice expression
    if args.expression:
        expr = " ".join(args.expression).strip()
        if expr:
            try:
                roll_expression(expr)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)

    # If nothing chosen
    if not (mode_key or args.list_spark or args.spark or args.wilderness or
            args.luck or args.unresolved or args.mood or
            (args.expression and " ".join(args.expression).strip())):
        print("Usage:")
        print("  roll [-oc|-onc|-ovl|-ol|-o|-ou|-ovu|-oni|-oi] [EXPR]")
        print("  roll -s SHEET|TABLE [--spark-file FILE] [--list-spark]")
        print("  roll -w -l -u -m")
        sys.exit(1)

if __name__ == "__main__":
    main()

