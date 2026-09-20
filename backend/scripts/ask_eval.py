"""Run real questions through the Ask router and show what the model decided.

This is how routing quality is judged: on the phrasings owners actually use,
against the real model, before any UI exists. It costs a fraction of a cent.

    OPENAI_API_KEY=... uv run python scripts/ask_eval.py
    uv run python scripts/ask_eval.py "kal ka cash counter" "and today?"

Each line shows the decision; a mismatch against the expectation (where one
is given) is marked so it stands out. Nothing here touches the database.
"""

import sys

from app.ask.llm import OpenAIRouter
from app.ask.periods import today_ist
from app.ask.router import RouterDecision

# (question, expected report or None, expected period kind or None)
CASES: list[tuple[str, str | None, str | None]] = [
    ("how were my sales last week", "sales_summary", "named"),
    ("which dish performed best since august this year", "top_items", "since"),
    ("which day was the highest revenue day since may this year", "best_days", "since"),
    ("give me all performance details about july", "period_summary", "month"),
    ("tell me everything about masala chai", "dish_details", None),
    ("how did chai do this month", "dish_details", "named"),
    ("top 5 items last month", "top_items", "named"),
    ("are we doing better than last week", "compare_periods", None),
    ("what should I reorder", "inventory_status", None),
    ("kal ka cash counter dikhao", "cash_counter", "named"),
    ("august mein kaunsi dish sabse zyada biki", "top_items", "month"),
    ("is mahine ka GST kitna bana", "gst", "named"),
    ("pichle hafte kitne orders cancel hue", "cancellations", "named"),
    ("compare august and september", None, None),  # unsupported
    ("which dish sells best on rainy days", None, None),  # unsupported
]

FOLLOW_UP = ("how did masala chai do this month", "and last month?")
# A complete question after a period-bearing one must not inherit that period.
NOT_A_FOLLOW_UP = ("kal ka cash counter", "when are we busiest?")


def show(question: str, decision: RouterDecision, expected_report, expected_kind) -> bool:
    period = decision.period.model_dump() if decision.period else None
    kind = period["kind"] if period else None
    ok = True
    if expected_report is not None and decision.report != expected_report:
        ok = False
    if expected_report is None and decision.action != "unsupported":
        ok = False
    if expected_kind is not None and kind != expected_kind:
        ok = False

    mark = "  " if ok else "!!"
    print(f"{mark} {question!r}")
    print(f"     action={decision.action} report={decision.report} period={period}")
    if decision.dish or decision.comparison or decision.limit:
        print(f"     dish={decision.dish!r} comparison={decision.comparison} limit={decision.limit}")
    if decision.message:
        print(f"     message={decision.message!r}")
    return ok


def main(argv: list[str]) -> int:
    from app.core.config import settings

    if not settings.OPENAI_API_KEY:
        print("Set OPENAI_API_KEY (in backend/.env or the environment) to run this.")
        return 2
    router = OpenAIRouter()
    today = today_ist()
    print(f"Today (IST): {today:%A %-d %B %Y}\n")

    if argv:
        previous = None
        previous_question = None
        for question in argv:
            decision = router.decide(question, previous, today, previous_question)
            show(question, decision, None, None)
            previous, previous_question = decision, question
        return 0

    failures = 0
    for question, expected_report, expected_kind in CASES:
        decision = router.decide(question, None, today)
        if not show(question, decision, expected_report, expected_kind):
            failures += 1

    first, second = FOLLOW_UP
    print("\nFollow-up:")
    d1 = router.decide(first, None, today)
    show(first, d1, "dish_details", None)
    d2 = router.decide(second, d1, today, first)
    ok = show(second, d2, "dish_details", "named") and d2.dish == d1.dish
    if not ok:
        failures += 1

    print("\nNot a follow-up:")
    first, second = NOT_A_FOLLOW_UP
    d1 = router.decide(first, None, today)
    show(first, d1, "cash_counter", "named")
    d2 = router.decide(second, d1, today, first)
    ok = show(second, d2, "peak_hours", None) and d2.period is None
    if not ok:
        print("     !! inherited the previous period")
        failures += 1

    total = len(CASES) + 4
    print(f"\n{total - failures}/{total} as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
