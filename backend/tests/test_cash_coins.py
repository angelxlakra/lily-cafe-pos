"""
Coins in the cash counter: ₹5, ₹2 and ₹1 rows beside the notes.

₹10 and ₹20 coins count in the ₹10 and ₹20 rows, so they need nothing new.
"""

from sqlalchemy import create_engine, inspect, text

from app.core import business_day
from app.db.session import ensure_cash_columns

TODAY = business_day.business_today()

NOTES = {f"{d}s": 0 for d in (500, 200, 100, 50, 20, 10)}


def _counts(stage: str, **counts) -> dict:
    return {f"{stage}_{k}": v for k, v in {**NOTES, **counts}.items()}


def test_coins_add_into_the_opening_and_closing_totals(client, owner_headers):
    opened = client.post(
        "/api/v1/cash-counter/open",
        json={"date": TODAY.isoformat(), **_counts("opening", **{"500s": 2, "5s": 12, "2s": 8, "1s": 15})},
        headers=owner_headers,
    )
    assert opened.status_code == 201, opened.text
    body = opened.json()
    # 2 × 500 + 12 × 5 + 8 × 2 + 15 × 1
    assert float(body["opening_balance"]) == 1091
    assert (body["opening_5s"], body["opening_2s"], body["opening_1s"]) == (12, 8, 15)

    closed = client.post(
        "/api/v1/cash-counter/close",
        json={"date": TODAY.isoformat(), **_counts("closing", **{"500s": 2, "5s": 1, "1s": 3})},
        headers=owner_headers,
    )
    assert closed.status_code == 200, closed.text
    assert float(closed.json()["closing_balance"]) == 1008
    assert closed.json()["closing_2s"] == 0


def test_a_client_from_before_coins_still_opens_the_day(client, owner_headers):
    response = client.post(
        "/api/v1/cash-counter/open",
        json={"date": TODAY.isoformat(), **_counts("opening", **{"100s": 3})},
        headers=owner_headers,
    )
    assert response.status_code == 201, response.text
    assert float(response.json()["opening_balance"]) == 300
    assert response.json()["opening_1s"] == 0


def test_an_older_database_gets_the_coin_columns_once(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE daily_cash_counter (id INTEGER PRIMARY KEY, opening_10s INTEGER)"))
        conn.execute(text("INSERT INTO daily_cash_counter (id, opening_10s) VALUES (1, 4)"))

    added = ensure_cash_columns(engine)
    assert sorted(added) == sorted(f"{s}_{d}s" for s in ("opening", "closing") for d in (5, 2, 1))
    assert ensure_cash_columns(engine) == []  # idempotent

    columns = {c["name"] for c in inspect(engine).get_columns("daily_cash_counter")}
    assert {"opening_1s", "closing_5s"} <= columns
    with engine.connect() as conn:
        # An existing day reads as no coins, not NULL.
        assert conn.execute(text("SELECT opening_5s FROM daily_cash_counter")).scalar() == 0
