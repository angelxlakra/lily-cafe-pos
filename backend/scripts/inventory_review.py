"""Print a worksheet for the inventory setup pass. Read-only.

There is deliberately no --apply. Every rule below is a *suggestion for a human*:
the data cannot tell a dead row apart from a real item the app has simply never
recorded a count for. SALT, MAIDA and the garbage bags all sit at zero with no
transactions, and none of them should be retired.

    uv run python scripts/inventory_review.py [path/to.db]

Defaults to DATABASE_URL, else restaurant.db. Against production, run it on the
machine that holds the volume:

    fly ssh console -C "python scripts/inventory_review.py /data/restaurant.db"
"""

import os
import re
import sqlite3
import sys

# Sauces, oils and spices nobody weighs — candidates for yes/no counting.
PRESENCE_WORDS = ("SAUCE", "OIL", "MAYO", "CHUTNEY", "MASALA", "ESSENCE",
                  "KETCHUP", "VINEGAR", "PASTE", "SYRUP", "POWDER")


def db_path() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    url = os.getenv("DATABASE_URL", "")
    return url.split("sqlite:///")[-1].lstrip("/") if url.startswith("sqlite") else "restaurant.db"


def section(title: str, rows: list, note: str = "") -> None:
    print(f"\n{title}  ({len(rows)})")
    print("-" * len(title))
    if note:
        print(f"  {note}")
    if not rows:
        print("  none")
        return
    for row in rows:
        print("  " + row)


def main() -> None:
    path = db_path()
    if not os.path.exists(path):
        sys.exit(f"No database at {path}")
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    q = lambda sql: db.execute(sql).fetchall()

    total, active = q("select count(*), sum(is_active) from inventory_items")[0]
    counts = q("select count(*) n from inventory_counts")[0]["n"] if q(
        "select name from sqlite_master where type='table' and name='inventory_counts'") else 0
    print(f"\nInventory review — {path}")
    print(f"{total} items, {active} active, {counts} saved counts")

    never = q("""
        select i.name, i.unit, i.current_quantity qty, coalesce(c.name,'—') cat
        from inventory_items i left join inventory_categories c on c.id = i.category_id
        where i.is_active = 1
          and not exists (select 1 from inventory_transactions t where t.item_id = i.id)
        order by cat, i.name
    """)
    section(
        "Never counted — do you still stock these?",
        [f"{r['cat']:<16} {r['name']:<30} {r['qty']} {r['unit']}" for r in never],
        "No transaction has ever touched these. That means untracked, NOT dead —\n"
        "  decide each one by hand. Retiring is deactivation, never deletion.",
    )

    # A quantity in the hundreds under "pcs" is almost always grams typed into the
    # wrong field; a gram figure in single digits is almost always a piece count.
    smells = q("""
        select name, unit, current_quantity qty,
               case when unit = 'pcs' and current_quantity >= 100 then 'pcs holding a weight?'
                    when unit = 'g'   and current_quantity between 1 and 20 then 'grams holding a count?'
               end why
        from inventory_items
        where is_active = 1
          and ((unit = 'pcs' and current_quantity >= 100)
            or (unit = 'g' and current_quantity between 1 and 20))
        order by why, current_quantity desc
    """)
    section(
        "Unit looks wrong",
        [f"{r['name']:<30} {r['qty']:>8} {r['unit']:<4} — {r['why']}" for r in smells],
        "Harmless today because nothing has a price. A 1000x error the moment one does.",
    )

    seen: dict[str, list[str]] = {}
    for r in q("select name from inventory_items where is_active = 1"):
        key = re.sub(r"[^a-z0-9]", "", r["name"].lower())
        seen.setdefault(key, []).append(r["name"])
    section(
        "Possible duplicates",
        [f"{' | '.join(names)}" for names in seen.values() if len(names) > 1],
        "Same name ignoring case, spacing and punctuation.",
    )

    presence = q(f"""
        select name, unit, current_quantity qty from inventory_items
        where is_active = 1 and current_quantity <= 1
          and ({' or '.join(f"name like '%{w}%'" for w in PRESENCE_WORDS)})
        order by name
    """)
    section(
        "Yes/no candidates",
        [f"{r['name']:<30} {r['qty']} {r['unit']}" for r in presence],
        "Sauces, oils and spices sitting at 0 or 1 — nobody weighs these.\n"
        "  A guess from the name, so confirm each one.",
    )

    print("\nNothing was changed. Work through these in the setup grid.\n")


if __name__ == "__main__":
    main()
