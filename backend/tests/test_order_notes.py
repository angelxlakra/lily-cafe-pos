"""
Kitchen notes on an order.

The waiter types an instruction ("no onion", "extra spicy") instead of a
customer name; it is stored on the order and printed in the NOTES section of
the kitchen/bar chit. Notes are per-round: each round of items prints its own
chit, so the note that prints is the one typed for that round.
"""

import importlib.util
import json
from io import BytesIO
from pathlib import Path

import pytest

from app import crud
from app.models import models
from app.models.print_job import PrintJob
from app.schemas.schemas import OrderCreate


def _order_payload(menu_item_id, notes=None, table_number=9, quantity=1):
    body = {
        "table_number": table_number,
        "items": [{"menu_item_id": menu_item_id, "quantity": quantity}],
    }
    if notes is not None:
        body["notes"] = notes
    return body


class TestNotesOnOrders:
    def test_note_is_saved_and_returned(self, client, sample_menu_items):
        response = client.post(
            "/api/v1/orders",
            json=_order_payload(sample_menu_items[0].id, notes="No onion, extra spicy"),
        )
        assert response.status_code == 201
        assert response.json()["notes"] == "No onion, extra spicy"

    def test_note_is_optional(self, client, sample_menu_items):
        response = client.post(
            "/api/v1/orders", json=_order_payload(sample_menu_items[0].id)
        )
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_note_is_length_limited(self, client, sample_menu_items):
        response = client.post(
            "/api/v1/orders",
            json=_order_payload(sample_menu_items[0].id, notes="x" * 501),
        )
        assert response.status_code == 422

    def test_second_round_replaces_the_note(self, client, sample_menu_items, test_db):
        """A chit prints per round, so the newest note is the one that prints."""
        first = client.post(
            "/api/v1/orders",
            json=_order_payload(sample_menu_items[0].id, notes="No onion"),
        )
        assert first.status_code == 201

        second = client.post(
            "/api/v1/orders",
            json=_order_payload(sample_menu_items[1].id, notes="Extra hot"),
        )
        assert second.status_code == 201
        assert second.json()["id"] == first.json()["id"]  # same active order
        assert second.json()["notes"] == "Extra hot"

    def test_second_round_without_a_note_clears_it(self, client, sample_menu_items):
        """Otherwise the previous round's note would reprint on the new chit."""
        client.post(
            "/api/v1/orders",
            json=_order_payload(sample_menu_items[0].id, notes="No onion"),
        )
        second = client.post(
            "/api/v1/orders", json=_order_payload(sample_menu_items[1].id)
        )
        assert second.status_code == 201
        assert second.json()["notes"] is None


class TestNoteReachesThePrinter:
    def test_note_is_in_the_queued_print_payload(
        self, client, test_db, sample_menu_items
    ):
        response = client.post(
            "/api/v1/orders",
            json=_order_payload(sample_menu_items[0].id, notes="No onion, extra spicy"),
        )
        assert response.status_code == 201

        jobs = test_db.query(PrintJob).all()
        assert jobs, "expected a chit print job to be queued"
        for job in jobs:
            assert json.loads(job.payload)["notes"] == "No onion, extra spicy"

    def test_payload_carries_null_when_there_is_no_note(
        self, client, test_db, sample_menu_items
    ):
        client.post("/api/v1/orders", json=_order_payload(sample_menu_items[0].id))

        jobs = test_db.query(PrintJob).all()
        assert jobs
        assert json.loads(jobs[0].payload)["notes"] is None


class TestChitRendering:
    """Both chit PDF paths must render with and without a note."""

    def _order(self, notes):
        order = models.Order(
            order_number="ORD-20260913-0001",
            table_number=7,
            subtotal=16000,
            gst_amount=800,
            total_amount=16800,
            notes=notes,
        )
        from datetime import datetime

        order.created_at = datetime.utcnow()
        order.order_items = [
            models.OrderItem(
                menu_item_name="Masala Dosa",
                quantity=2,
                unit_price=8000,
                subtotal=16000,
                is_beverage=False,
                is_parcel=False,
            )
        ]
        return order

    @pytest.mark.parametrize("paper_size", ["80mm", "58mm"])
    @pytest.mark.parametrize(
        "notes",
        [
            None,
            "No onion",
            "No onion, extra spicy, and please rush this one for the party table",
            "Supercalifragilisticexpialidocioussupercalifragilisticexpialidocious",
        ],
    )
    def test_chit_pdf_renders(self, paper_size, notes):
        from app.utils.pdf_generator import generate_order_chit_pdf

        buffer = BytesIO()
        generate_order_chit_pdf(self._order(notes), buffer, paper_size=paper_size)
        assert buffer.getvalue().startswith(b"%PDF")


# The print relay agent lives outside the backend package (repo-root /agent),
# so load its renderer by path rather than importing it.
_RENDERER_PATH = Path(__file__).resolve().parents[2] / "agent" / "chit_renderer.py"


@pytest.fixture(scope="module")
def wrap():
    spec = importlib.util.spec_from_file_location("chit_renderer", _RENDERER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._wrap


class TestEscposWrapping:
    """The thermal renderer wraps notes itself; printers do not."""

    def test_wraps_on_word_boundaries(self, wrap):
        assert wrap("No onion, extra spicy", 10) == ["No onion,", "extra", "spicy"]

    def test_hard_splits_a_word_longer_than_the_line(self, wrap):
        assert wrap("abcdefghijkl", 5) == ["abcde", "fghij", "kl"]

    def test_empty_note_produces_no_lines(self, wrap):
        assert wrap("", 10) == []

    def test_no_line_exceeds_the_width(self, wrap):
        note = "No onion, extra spicy, serve after the main course please"
        assert all(len(line) <= 14 for line in wrap(note, 14))

    def test_no_characters_are_lost(self, wrap):
        note = "No onion, extra spicy, serve after the main course please"
        assert "".join(wrap(note, 14)).replace(" ", "") == note.replace(" ", "")
