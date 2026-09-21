"""What the model is asked to produce, and the prompt that asks for it.

The model's entire output is a RouterDecision: which report, which dish (as
the owner wrote it), which period (named, or explicit dates the owner
actually said), and nothing else. It is validated against a strict JSON
schema, so a malformed answer is a rejected request, not a wrong number.
"""

from datetime import date
from typing import Literal, Protocol

from pydantic import BaseModel, Field, TypeAdapter

from app.ask.periods import NamedPeriod, Period
from app.ask.reports import REPORT_IDS, Comparison, catalogue_for_prompt

_ISO_DATE = r"^\d{4}-\d{2}-\d{2}$"


# The model-facing period types use plain strings for dates: strict
# structured output supports `pattern`, and the strings are turned into real
# dates by the periods module, which validates them properly.
class NamedOut(BaseModel):
    kind: Literal["named"]
    name: NamedPeriod


class MonthOut(BaseModel):
    kind: Literal["month"]
    year: int
    month: int


class RangeOut(BaseModel):
    kind: Literal["range"]
    start: str = Field(pattern=_ISO_DATE)
    end: str = Field(pattern=_ISO_DATE)


class SinceOut(BaseModel):
    kind: Literal["since"]
    start: str = Field(pattern=_ISO_DATE)


class DayOut(BaseModel):
    kind: Literal["day"]
    date: str = Field(pattern=_ISO_DATE)


# No declared discriminator: that would emit `oneOf`, which OpenAI's strict
# mode rejects. Pydantic still picks the right member from the `kind` literal.
PeriodOut = NamedOut | MonthOut | RangeOut | SinceOut | DayOut

ReportId = Literal[REPORT_IDS]


class RouterDecision(BaseModel):
    action: Literal["report", "clarify", "unsupported"]
    report: ReportId | None
    period: PeriodOut | None
    dish: str | None
    comparison: Comparison | None
    limit: int | None
    # clarify: the question to put to the owner. unsupported: what cannot
    # be done and which report is closest. Never contains figures.
    message: str | None


_period_adapter = TypeAdapter(Period)


def to_period_spec(out: NamedOut | MonthOut | RangeOut | SinceOut | DayOut):
    """Model output → the validated period spec the resolver takes."""
    return _period_adapter.validate_python(out.model_dump())


class Router(Protocol):
    def decide(
        self,
        question: str,
        previous: RouterDecision | None,
        today: date,
        previous_question: str | None = None,
    ) -> RouterDecision: ...


# ----------------------------------------------------------------------
# Prompt
# ----------------------------------------------------------------------

_RULES = """You route a cafe owner's question to one report from a fixed catalogue. You never answer the question yourself and you never produce numbers, dates of your own invention, or analysis.

Reports:
{catalogue}

Rules:
1. Pick exactly one report id. If no report answers the question, set action="unsupported" and in message say in one sentence what cannot be done and which report is closest.
2. Period. For relative phrases — today, yesterday, this week, last week, this month, last month, this year, last 7 days, last 30 days, all time — use kind="named" and never convert them to dates yourself. For a month the owner names ("August", "in July") use kind="month"; a month with no year means the most recent one that has already started. For "since <month or date>" use kind="since" with the first day of that month or that date. For an explicit range use kind="range". For one specific date use kind="day". If the owner gives no period, leave period null — a sensible default is applied and shown to them.
3. Dish. If the question is about one particular dish, use report="dish_details" and copy the dish name exactly as the owner wrote it, including spelling and language. Do not correct, translate or complete it; matching happens later.
4. Comparison. Only report="compare_periods" takes one: "vs yesterday" → today_vs_yesterday, "vs last week" → this_week_vs_last_week, "vs last month" → this_month_vs_last_month. Any other comparison (two named months, two dishes) is unsupported; say the owner can ask for each separately.
5. Follow-ups. A message is a follow-up only when it cannot stand on its own: a fragment such as "and September?", "what about coffee?", "last week instead", "top 5", or a bare dish name answering a clarification. For those, keep everything else from the previous decision. A complete new question ("when are we busiest?", "how much GST this month?") stands alone: decide it fresh and do not inherit the previous period or dish.
6. The owner may write in Hindi, Hinglish (Roman-script Hindi) or English. Understand all three. Keep dish names as written.
7. Use action="clarify" only when the question is genuinely ambiguous between two reports; put one short question in message. Never clarify just because the period is missing.
8. limit: set only when the owner asks for a specific count ("top 5", "top 3"); otherwise null.
9. Every field must be present; use null for anything that does not apply."""

_EXAMPLES = """Examples (question → decision):

"how were sales last week" → {"action":"report","report":"sales_summary","period":{"kind":"named","name":"last_week"},"dish":null,"comparison":null,"limit":null,"message":null}
"which dish performed best since august this year" → {"action":"report","report":"top_items","period":{"kind":"since","start":"{august_first}"},"dish":null,"comparison":null,"limit":null,"message":null}
"which day was the highest revenue day since may" → {"action":"report","report":"best_days","period":{"kind":"since","start":"{may_first}"},"dish":null,"comparison":null,"limit":null,"message":null}
"give me all details about july" → {"action":"report","report":"period_summary","period":{"kind":"month","year":{year},"month":7},"dish":null,"comparison":null,"limit":null,"message":null}
"how did masala chai do this month" → {"action":"report","report":"dish_details","period":{"kind":"named","name":"this_month"},"dish":"masala chai","comparison":null,"limit":null,"message":null}
"august mein kaunsi dish sabse zyada biki" → {"action":"report","report":"top_items","period":{"kind":"month","year":{year},"month":8},"dish":null,"comparison":null,"limit":null,"message":null}
"kal ka cash counter" → {"action":"report","report":"cash_counter","period":{"kind":"named","name":"yesterday"},"dish":null,"comparison":null,"limit":null,"message":null}
"top 5 items" → {"action":"report","report":"top_items","period":null,"dish":null,"comparison":null,"limit":5,"message":null}
"are we doing better than last week" → {"action":"report","report":"compare_periods","period":null,"dish":null,"comparison":"this_week_vs_last_week","limit":null,"message":null}
(previous: dish_details, dish "masala chai", period this_month) "and last month?" → {"action":"report","report":"dish_details","period":{"kind":"named","name":"last_month"},"dish":"masala chai","comparison":null,"limit":null,"message":null}
"compare august and september" → {"action":"unsupported","report":null,"period":null,"dish":null,"comparison":null,"limit":null,"message":"I can only compare this month with last month, this week with last week, or today with yesterday. Ask for August and September separately and I will show each."}
"which dish sells best on rainy days" → {"action":"unsupported","report":null,"period":null,"dish":null,"comparison":null,"limit":null,"message":"I have no weather data. The closest is best selling items for a period."}"""


def build_system_prompt(today: date) -> str:
    year = today.year
    august = date(year if today.month >= 8 else year - 1, 8, 1)
    may = date(year if today.month >= 5 else year - 1, 5, 1)
    examples = (
        _EXAMPLES.replace("{august_first}", august.isoformat())
        .replace("{may_first}", may.isoformat())
        .replace("{year}", str(year))
    )
    return (
        _RULES.format(catalogue=catalogue_for_prompt())
        + "\n\n"
        + examples
        + f"\n\nToday is {today:%A %-d %B %Y} (IST)."
    )


def build_user_message(
    question: str, previous: RouterDecision | None, previous_question: str | None
) -> str:
    if previous is None:
        return f"Question: {question}"
    parts = []
    if previous_question:
        parts.append(f"Previous question: {previous_question}")
    parts.append(f"Previous decision: {previous.model_dump_json()}")
    parts.append(f"Question: {question}")
    return "\n".join(parts)
