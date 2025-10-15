#!/usr/bin/env python3
import argparse
import json
import os
import random
import re
import sys
import unicodedata

# ---------------- Dice & Oracle ----------------

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


def oracle(mode: str):
    r = random.randint(1, 6)
    if mode == "standard":      # 1-3 yes, 4-5 no, 6 twist
        verdict = "YES" if r <= 3 else ("NO" if r <= 5 else "TWIST")
    elif mode == "likely":      # 1-4 yes, 5 no, 6 twist
        verdict = "YES" if r <= 4 else ("NO" if r == 5 else "TWIST")
    elif mode == "unlikely":    # 1-2 yes, 3-5 no, 6 twist
        verdict = "YES" if r <= 2 else ("NO" if r <= 5 else "TWIST")
    else:
        raise ValueError("Unknown oracle mode.")
    print(f"🔮 Oracle ({mode}) d6 → {r}: {verdict}")
    return r, verdict


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

        # Sheet header
        if ":" in raw and ";" not in raw:
            current_sheet = raw.split(":")[0].strip()
            sheets.setdefault(current_sheet, {})
            i += 1
            continue

        # Table start
        if raw.count(";") >= 2:
            parts = [p.strip() for p in raw.split(";")]
            if len(parts) >= 3 and parts[0] == "" and parts[1] and parts[2] == "":
                table_name = parts[1]

                # Header
                col1, col2 = "Col1", "Col2"
                if i + 1 < len(lines):
                    hdr = [p.strip() for p in lines[i+1].split(";")]
                    if len(hdr) >= 3:
                        col1, col2 = hdr[1], hdr[2]

                # Rows
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

    # Sheet match
    for sheet, tables in spark_data.items():
        if _norm(sheet) == key:
            table_name = random.choice(list(tables.keys()))
            return sheet, table_name, tables[table_name]

    # Table match
    for sheet, tables in spark_data.items():
        for table_name, table in tables.items():
            if _norm(table_name) == key:
                return sheet, table_name, table

    # Fuzzy
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
        description="Roll dice expressions, a yes/no oracle, and Spark tables."
    )

    g = p.add_mutually_exclusive_group()
    g.add_argument("-o",  "--oracle", action="store_true", help="Standard oracle (1–3 yes, 4–5 no, 6 twist)")
    g.add_argument("-ol", "--oracle-likely", action="store_true", help="Likely oracle (1–4 yes, 5 no, 6 twist)")
    g.add_argument("-ou", "--oracle-unlikely", action="store_true", help="Unlikely oracle (1–2 yes, 3–5 no, 6 twist)")

    # Spark options
    p.add_argument("-s", "--spark", metavar="SHEET|TABLE",
                   help="Roll a Spark table: pass a TABLE to roll it, or a SHEET to pick a random table within it.")
    p.add_argument("--spark-file", default=os.environ.get("SPARK_FILE", "Spark Tables PL.csv"),
                   help="Path to Spark data (CSV from Numbers or JSON). Defaults to 'Spark Tables PL.csv' or $SPARK_FILE.")
    p.add_argument("--list-spark", action="store_true",
                   help="List available Spark sheets and tables.")

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

    # Spark listing
    if args.list_spark:
        try:
            data = load_spark(args.spark_file)
            print("📚 Spark sheets & tables:")
            print(list_spark(data))
        except Exception as e:
            print(f"Error loading spark file: {e}")
        # continue — not exit, so user can combine with other options

    # Oracle
    mode = "standard" if args.oracle else (
        "likely" if args.oracle_likely else (
            "unlikely" if args.oracle_unlikely else None
        )
    )
    if mode:
        oracle(mode)

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
    if not (args.list_spark or mode or args.spark or args.wilderness or
            args.luck or args.unresolved or args.mood or
            (args.expression and " ".join(args.expression).strip())):
        print("Usage:")
        print("  roll [-o|-ol|-ou|-w|-l|-u|-m] [EXPR]")
        print("  roll -s SHEET|TABLE [--spark-file FILE] [--list-spark]")
        print("Examples:")
        print("  roll d20 + d12")
        print("  roll -o")
        print("  roll -s DRAMA")
        print("  roll -w -m -l -u")
        sys.exit(1)


if __name__ == "__main__":
    main()

