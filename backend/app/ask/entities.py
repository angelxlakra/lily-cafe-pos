"""Resolve what the owner called a dish to the exact menu item name.

The analytics tools match menu items by exact name, and the model is told to
repeat the owner's words rather than guess a canonical name. So "chai" has to
become "Masala Chai" here — and when it could equally be "Ginger Chai", the
owner is asked rather than shown the wrong dish's numbers.
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

# Below this, a candidate is not considered a plausible match at all.
_MIN_SCORE = 0.6
# A single candidate needs to beat the runner-up by this much to be chosen
# without asking; otherwise the choice is the owner's.
_CLEAR_MARGIN = 0.15


@dataclass(frozen=True)
class DishMatch:
    name: str | None
    candidates: list[str] = field(default_factory=list)

    @property
    def is_resolved(self) -> bool:
        return self.name is not None

    @property
    def is_ambiguous(self) -> bool:
        return self.name is None and len(self.candidates) > 1


def match_dish(query: str, menu_names: list[str]) -> DishMatch:
    wanted = _normalize(query)
    if not wanted:
        return DishMatch(None, [])

    scored = sorted(
        ((_score(wanted, _normalize(name)), name) for name in menu_names),
        key=lambda pair: pair[0],
        reverse=True,
    )
    plausible = [(score, name) for score, name in scored if score >= _MIN_SCORE]
    if not plausible:
        return DishMatch(None, [])

    best_score, best_name = plausible[0]
    if best_score >= 1.0:
        return DishMatch(best_name, [best_name])

    runner_up = plausible[1][0] if len(plausible) > 1 else 0.0
    if best_score - runner_up >= _CLEAR_MARGIN:
        return DishMatch(best_name, [best_name])

    return DishMatch(None, [name for _, name in plausible[:5]])


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def _score(wanted: str, candidate: str) -> float:
    if wanted == candidate:
        return 1.0
    wanted_words = set(wanted.split())
    candidate_words = set(candidate.split())
    # Every word the owner said appears in the dish name ("masala chai" in
    # "Masala Chai Large"), or the dish name is contained in what they said.
    if wanted_words and wanted_words <= candidate_words:
        return 0.9
    if candidate_words and candidate_words <= wanted_words:
        return 0.9
    return SequenceMatcher(None, wanted, candidate).ratio()
