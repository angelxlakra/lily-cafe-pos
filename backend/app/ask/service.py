"""Turn a question into a computed report.

The model decides; this module checks the decision against the catalogue,
fills in defaults, resolves the period and the dish, and runs the report.
Every clarification the owner sees is generated here, from real menu names
and real period errors — the model's message is only used for the two
things it alone knows: that a question is ambiguous, or unanswerable.
"""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ask.entities import match_dish
from app.ask.periods import NamedSpec, PeriodError, ResolvedPeriod, resolve, today_ist
from app.ask.reports import REPORTS, Report, ReportContext
from app.ask.router import Router, RouterDecision, to_period_spec
from app.models.models import MenuItem

DEFAULT_LIMIT = 10
MAX_LIMIT = 50


class AskResponse(BaseModel):
    kind: Literal["report", "clarify", "unsupported"]
    # report
    report_id: str | None = None
    title: str | None = None
    period_label: str | None = None
    dish: str | None = None
    data: dict[str, Any] | None = None
    # clarify / unsupported
    message: str | None = None
    candidates: list[str] = []
    # Echoed back so the client can send it with the next question.
    decision: RouterDecision | None = None


def ask(
    db: Session,
    question: str,
    router: Router,
    previous: RouterDecision | None = None,
    previous_question: str | None = None,
    today: date | None = None,
) -> AskResponse:
    today = today or today_ist()
    decision = router.decide(question, previous, today, previous_question)

    if decision.action == "unsupported":
        return AskResponse(
            kind="unsupported",
            message=decision.message or "I can't answer that from the reports I have.",
            decision=decision,
        )
    if decision.action == "clarify":
        return AskResponse(
            kind="clarify",
            message=decision.message or "Could you say a bit more about what you'd like to see?",
            decision=decision,
        )

    report = REPORTS.get(decision.report or "")
    if report is None:
        return AskResponse(
            kind="unsupported",
            message="I can't answer that from the reports I have.",
            decision=decision,
        )

    try:
        period = _resolve_period(report, decision, today)
    except PeriodError as error:
        return AskResponse(kind="clarify", message=str(error), decision=decision)

    dish = None
    if report.needs_dish:
        outcome = _resolve_dish(db, decision.dish)
        if isinstance(outcome, AskResponse):
            outcome.decision = decision
            return outcome
        dish = outcome

    if report.needs_comparison and decision.comparison is None:
        return AskResponse(
            kind="clarify",
            message=(
                "I can compare today with yesterday, this week with last week, "
                "or this month with last month. Which one?"
            ),
            decision=decision,
        )

    limit = max(1, min(decision.limit or DEFAULT_LIMIT, MAX_LIMIT))
    data = report.run(db, ReportContext(period, dish, decision.comparison, limit))

    return AskResponse(
        kind="report",
        report_id=report.id,
        title=report.title,
        period_label=period.label if period else None,
        dish=dish,
        data=data,
        decision=_normalized(decision, report, dish),
    )


def _resolve_period(report: Report, decision: RouterDecision, today: date) -> ResolvedPeriod | None:
    if report.period == "none":
        return None

    if decision.period is not None:
        spec = to_period_spec(decision.period)
    elif report.default_period is not None:
        spec = NamedSpec(name=report.default_period)
    else:  # pragma: no cover — every ranged report declares a default
        raise PeriodError("Which period would you like?")

    resolved = resolve(spec, today)
    if report.period == "single_day" and not resolved.is_single_day:
        raise PeriodError(
            f"{report.title} is for one day at a time. Which day would you like?"
        )
    return resolved


def _resolve_dish(db: Session, wanted: str | None) -> str | AskResponse:
    if not wanted:
        return AskResponse(kind="clarify", message="Which dish would you like to see?")

    menu = [name for (name,) in db.query(MenuItem.name).all()]
    match = match_dish(wanted, menu)
    if match.is_resolved:
        return match.name
    if match.is_ambiguous:
        return AskResponse(
            kind="clarify",
            message=f"Which one did you mean by “{wanted}”?",
            candidates=match.candidates,
        )
    return AskResponse(
        kind="clarify",
        message=f"I couldn't find a dish called “{wanted}” on the menu.",
        candidates=match.candidates,
    )


def _normalized(decision: RouterDecision, report: Report, dish: str | None) -> RouterDecision:
    """The decision as carried into the next turn: resolved dish, real report."""
    return decision.model_copy(update={"report": report.id, "dish": dish or decision.dish})
