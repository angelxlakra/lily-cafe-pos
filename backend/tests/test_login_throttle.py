"""Brute-force protection on the sign-in paths.

Both /api/v1/auth/login and the MCP consent page authenticate the same fixed
owner/admin credentials, so they share one per-source limiter.
"""

import pytest

from app.core.config import settings
from app.core.login_throttle import LOCKED_OUT_MESSAGE, LoginThrottle, login_throttle
from tests import test_mcp_oauth as oauth
from tests.test_mcp_oauth import _approve, _owner_credentials, _pkce, _register, _start_authorization

LOGIN_URL = "/api/v1/auth/login"
LIMIT = settings.LOGIN_MAX_FAILURES
WINDOW = settings.LOGIN_FAILURE_WINDOW_MINUTES * 60


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    """Drive the shared limiter's clock so lockout expiry is testable."""
    fake = FakeClock()
    monkeypatch.setattr(login_throttle, "_clock", fake)
    return fake


def _login(client, password="wrong", username=None, headers=None):
    return client.post(
        LOGIN_URL,
        json={"username": username or settings.OWNER_USERNAME, "password": password},
        headers=headers or {},
    )


# ============================================================================
# Limiter unit tests
# ============================================================================


class TestLoginThrottle:
    def test_locks_after_max_failures_in_window(self):
        clock = FakeClock()
        throttle = LoginThrottle(max_failures=3, window_seconds=60, clock=clock)

        for _ in range(2):
            throttle.record_failure("1.2.3.4")
        assert not throttle.is_locked("1.2.3.4")

        throttle.record_failure("1.2.3.4")
        assert throttle.is_locked("1.2.3.4")
        assert throttle.retry_after("1.2.3.4") == 61
        # Other sources are unaffected.
        assert not throttle.is_locked("5.6.7.8")

    def test_lockout_expires_when_failures_age_out(self):
        clock = FakeClock()
        throttle = LoginThrottle(max_failures=3, window_seconds=60, clock=clock)

        throttle.record_failure("ip")
        clock.advance(30)
        throttle.record_failure("ip")
        throttle.record_failure("ip")
        assert throttle.is_locked("ip")

        # Just before the first failure leaves the window: still locked.
        clock.advance(29)
        assert throttle.is_locked("ip")
        # Once it has aged out only two count, which is below the threshold,
        # even though the last two failures are still recent.
        clock.advance(2)
        assert not throttle.is_locked("ip")

    def test_success_clears_history(self):
        throttle = LoginThrottle(max_failures=3, window_seconds=60, clock=FakeClock())
        throttle.record_failure("ip")
        throttle.record_failure("ip")
        throttle.record_success("ip")
        throttle.record_failure("ip")
        throttle.record_failure("ip")
        assert not throttle.is_locked("ip")


# ============================================================================
# /api/v1/auth/login
# ============================================================================


class TestLoginEndpointThrottle:
    def test_n_failures_then_lockout(self, client, clock):
        for _ in range(LIMIT):
            assert _login(client).status_code == 401

        locked = _login(client)
        assert locked.status_code == 429
        assert locked.json()["detail"] == LOCKED_OUT_MESSAGE
        assert int(locked.headers["Retry-After"]) > 0

        # The correct password does not get through while locked out either.
        assert _login(client, settings.OWNER_PASSWORD).status_code == 429

    def test_lockout_response_is_the_same_for_any_username(self, client, clock):
        for _ in range(LIMIT):
            _login(client)

        real = _login(client, username=settings.OWNER_USERNAME)
        fake = _login(client, username="no-such-user")
        assert real.status_code == fake.status_code == 429
        assert real.json() == fake.json()

    def test_lockout_expires(self, client, clock):
        for _ in range(LIMIT):
            _login(client)
        assert _login(client).status_code == 429

        clock.advance(WINDOW - 1)
        assert _login(client).status_code == 429

        clock.advance(2)
        assert _login(client, settings.OWNER_PASSWORD).status_code == 200

    def test_successful_login_unaffected_below_threshold(self, client, clock):
        for _ in range(LIMIT - 1):
            assert _login(client).status_code == 401

        ok = _login(client, settings.OWNER_PASSWORD)
        assert ok.status_code == 200
        assert "access_token" in ok.json()

        # Success resets the count, so the source has its full allowance back.
        for _ in range(LIMIT - 1):
            assert _login(client).status_code == 401
        assert _login(client, settings.ADMIN_PASSWORD, settings.ADMIN_USERNAME).status_code == 200

    def test_keyed_on_fly_client_ip_not_socket(self, client, clock):
        attacker = {"Fly-Client-IP": "203.0.113.9"}
        for _ in range(LIMIT):
            _login(client, headers=attacker)
        assert _login(client, headers=attacker).status_code == 429

        # Same socket (the proxy), different real client: not locked out.
        other = {"Fly-Client-IP": "198.51.100.4"}
        assert _login(client, settings.OWNER_PASSWORD, headers=other).status_code == 200

    def test_x_forwarded_for_first_hop_is_used(self, client, clock):
        headers = {"X-Forwarded-For": "203.0.113.9, 10.0.0.1"}
        for _ in range(LIMIT):
            _login(client, headers=headers)
        assert _login(client, headers=headers).status_code == 429
        assert _login(client, headers={"X-Forwarded-For": "203.0.113.9"}).status_code == 429
        assert _login(client, headers={"X-Forwarded-For": "10.0.0.1"}).status_code == 401


# ============================================================================
# MCP consent page shares the limiter
# ============================================================================


@pytest.fixture
def mcp_client(db_session, monkeypatch):
    yield from oauth.client.__wrapped__(db_session, monkeypatch)


def _fresh_txn(mcp_client):
    registration = _register(mcp_client)
    _, challenge = _pkce()
    return _start_authorization(mcp_client, registration["client_id"], challenge)


class TestConsentThrottle:
    def test_fresh_transactions_do_not_reset_the_count(self, mcp_client, clock):
        # Every attempt on its own transaction, so the per-transaction cap
        # never trips: only the per-source limiter can stop this.
        for _ in range(LIMIT):
            assert _approve(mcp_client, _fresh_txn(mcp_client), "owner", "wrong").status_code == 401

        locked = _approve(mcp_client, _fresh_txn(mcp_client), *_owner_credentials())
        assert locked.status_code == 429
        assert LOCKED_OUT_MESSAGE in locked.text
        assert "Retry-After" in locked.headers

    def test_lockout_expires_on_consent_page(self, mcp_client, clock):
        for _ in range(LIMIT):
            _approve(mcp_client, _fresh_txn(mcp_client), "owner", "wrong")
        assert _approve(mcp_client, _fresh_txn(mcp_client), *_owner_credentials()).status_code == 429

        clock.advance(WINDOW + 1)
        assert _approve(mcp_client, _fresh_txn(mcp_client), *_owner_credentials()).status_code == 302

    def test_owner_approves_normally_below_threshold(self, mcp_client, clock):
        for _ in range(LIMIT - 1):
            _approve(mcp_client, _fresh_txn(mcp_client), "owner", "wrong")
        assert _approve(mcp_client, _fresh_txn(mcp_client), *_owner_credentials()).status_code == 302

    def test_lockout_response_does_not_reveal_which_login_exists(self, mcp_client, clock):
        for _ in range(LIMIT):
            _approve(mcp_client, _fresh_txn(mcp_client), "owner", "wrong")
        txn = _fresh_txn(mcp_client)
        wrong_owner = _approve(mcp_client, txn, settings.OWNER_USERNAME, "wrong")
        as_admin = _approve(mcp_client, txn, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
        assert wrong_owner.status_code == as_admin.status_code == 429
        assert wrong_owner.text == as_admin.text

    def test_login_failures_count_against_the_consent_page(self, client, mcp_client, clock):
        """The consent page is not a way around the login limiter."""
        for _ in range(LIMIT):
            _login(client)
        assert _approve(mcp_client, _fresh_txn(mcp_client), *_owner_credentials()).status_code == 429

    def test_consent_failures_count_against_login(self, client, mcp_client, clock):
        """...and vice versa."""
        for _ in range(LIMIT):
            _approve(mcp_client, _fresh_txn(mcp_client), "owner", "wrong")
        assert _login(client, settings.OWNER_PASSWORD).status_code == 429
