from app.ask.entities import match_dish

MENU = [
    "Masala Chai",
    "Ginger Chai",
    "Filter Coffee",
    "Cold Coffee",
    "Masala Dosa",
    "Paneer Butter Masala",
    "Veg Fried Rice",
]


def test_exact_name_case_insensitive():
    assert match_dish("masala dosa", MENU).name == "Masala Dosa"


def test_word_subset_resolves_when_unique():
    assert match_dish("filter coffee", MENU).name == "Filter Coffee"
    assert match_dish("fried rice", MENU).name == "Veg Fried Rice"


def test_single_word_shared_by_two_dishes_is_ambiguous():
    """'chai' fits Masala Chai and Ginger Chai equally — ask, don't guess."""
    m = match_dish("chai", MENU)
    assert not m.is_resolved
    assert m.is_ambiguous
    assert set(m.candidates) == {"Masala Chai", "Ginger Chai"}


def test_coffee_alone_is_ambiguous():
    m = match_dish("coffee", MENU)
    assert m.is_ambiguous
    assert set(m.candidates) == {"Filter Coffee", "Cold Coffee"}


def test_masala_alone_is_ambiguous_across_categories():
    m = match_dish("masala", MENU)
    assert m.is_ambiguous
    assert "Masala Chai" in m.candidates and "Paneer Butter Masala" in m.candidates


def test_typo_resolves_to_the_only_close_name():
    assert match_dish("panner butter masala", MENU).name == "Paneer Butter Masala"


def test_nonsense_matches_nothing():
    m = match_dish("quantum burrito", MENU)
    assert not m.is_resolved
    assert m.candidates == []


def test_punctuation_and_spacing_are_ignored():
    assert match_dish("  Masala-Chai!! ", MENU).name == "Masala Chai"


def test_empty_query():
    assert match_dish("   ", MENU).name is None
